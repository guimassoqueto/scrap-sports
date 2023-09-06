from asyncio import Semaphore, create_task, gather
import math
from urllib.parse import urljoin
from aiohttp import ClientSession
from app.db.postgres_db import insert_products
from app.scraper.scraper import Scraper
from app.settings import NIKE_OFFERS_API
from fake_useragent import UserAgent


def get_nike_api_url(page_number: int):
    url = NIKE_OFFERS_API.replace("&page=", f"&page={page_number}")
    return url


def header() -> dict:
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection':	'keep-alive',
        'Host':	'www.nike.com.br',
        'If-None-Match': "2473a-/sPrqiNGsqYIZeDxEz+87lTUt3M",
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'TE':	'trailers',
        'Upgrade-Insecure-Requests':	'1',
        'User-Agent': UserAgent().random
    }


async def get_urls() -> list:
    headers = header()
    async with ClientSession(headers=headers) as session:
        first_page = get_nike_api_url(0)
        async with session.get(first_page) as response:
            assert response.status == 200, "Status Code must be 200"
            try:
                data = await response.json()
                products_per_pages = data['pageProps']['dehydratedState']['queries'][0]['state']['data']['pages'][0]['productsPerPage']
                total_products = data['pageProps']['dehydratedState']['queries'][0]['state']['data']['pages'][0]['quantity']
                total_pages = math.ceil(total_products / products_per_pages) + 1
                return [ get_nike_api_url(i) for i in range(0, total_pages) ]
            except Exception:
                return [ first_page ]


class Nike:
    @staticmethod
    async def exec(concurrency_limit: Semaphore):
        urls = await get_urls()
        tasks = []
        for url in urls:
            scraper = ScraperNike()
            task = create_task(scraper.scrap(url, concurrency_limit))
            tasks.append(task)
        result = await gather(*tasks)
        return result


class ScraperNike(Scraper):
    async def scrap(self, url: str, concurrency_limit: Semaphore) -> None:
        headers = header()
        async with concurrency_limit:
            async with ClientSession(headers=headers) as session:
                async with session.get(url) as response:
                    assert response.status == 200, "Status Code must be 200"
                    try:
                        data = await response.json()
                        products = self.parse_data(data)
                        await insert_products(products)
                    except Exception as e:
                        print(e)


    def parse_data(self, data) -> dict:
        products_raw = data['pageProps']['dehydratedState']['queries'][0]['state']['data']['pages'][0]['products']
        products = []
        for product in products_raw:
            try:
                has_stock = product["details"]["hasStock"]
                if has_stock:
                    products.append(self.format_product(product))
            except Exception as e:
                print(e)
                continue
        return products
    

    def format_product(self, product: dict) -> dict:
        details = product["details"]
        category = f"{details['modality']} {' '.join(details['categories'])} {' '.join(details['genders'])}"
        reviews = details["reviews"]
        return {
            'product_url': urljoin('https://www.nike.com.br/', product['url']).replace("'", "''"),
            'title': str(product['name']).replace("'", "''"),
            'category': category,
            "free_shipping": False,
            'image_url': f"https://imgnike-a.akamaihd.net/1080x1080/{product['id']}.jpg",
            "reviews": reviews,
            'discount': round((1 - (product['price'] / product['oldPrice'])) * 100),
            'price': product['price'],
            'previous_price': product['oldPrice']
        }