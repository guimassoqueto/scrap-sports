from asyncio import Semaphore, create_task, gather
from aiohttp import ClientSession
from urllib.parse import urljoin
from app.db.postgres_db import insert_products
from app.scraper.scraper import Scraper
from app.settings import ADIDAS_OFFERS_API


def get_adidas_api_url(page_number: int):
    url = ADIDAS_OFFERS_API.replace("&start=", f"&start={page_number}")
    return url


def header() -> dict:
    return {
        'Accept':	'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Encoding':	'gzip, deflate, br',
        'Accept-Language':	'en-US,en;q=0.5',
        'Connection':	'keep-alive',
        'Host':	'www.adidas.com.br',
        'Sec-Fetch-Dest':	'document',
        'Sec-Fetch-Mode':	'navigate',
        'Sec-Fetch-Site':	'none',
        'Sec-Fetch-User':	'?1',
        'TE':	'trailers',
        'Upgrade-Insecure-Requests':	'1',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0'
    }


async def get_urls() -> list:
    headers = header()
    async with ClientSession(headers=headers) as session:
        first_page = get_adidas_api_url(0)
        async with session.get(first_page) as response:
            assert response.status == 200, "Status Code must be 200"
            try:
                data = await response.json()
                total_products = data["raw"]["itemList"]["count"]
                return [get_adidas_api_url(i) for i in range(0, total_products, 48)]
            except Exception as e:
                return [ first_page ]
    

class Adidas:
    @staticmethod
    async def exec(concurrency_limit: Semaphore):
        urls = await get_urls()
        tasks = []
        for url in urls:
            scraper = ScraperAdidas()
            task = create_task(scraper.scrap(url, concurrency_limit))
            tasks.append(task)
        result = await gather(*tasks)
        return result


class ScraperAdidas(Scraper):
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
        products_raw = data["raw"]["itemList"]["items"]
        products = []
        for product in products_raw:
            try:
                products.append(self.format_product(product))
            except Exception as e:
                print(e)
                continue
        return products
    

    def format_product(self, product: dict) -> dict:
        category = f"{product['division']} {product['category']} {product['sport']} {product['subTitle']}".replace("Homem", "Masculino").replace("Mulher", "Feminino")
        return {
            "id": urljoin("https://adidas.com.br", product["link"]),
            "title": product["altText"].replace("'", "''"),
            "category": category,
            "reviews": product["ratingCount"],
            "free_shipping": False,
            "image_url": product["image"]["src"].replace("w_280,h_280", "w_766,h_766"),
            "price": product["salePrice"],
            "previous_price": product["price"],
            "discount": round((1 - (product['salePrice'] / product['price'])) * 100),
        }
    