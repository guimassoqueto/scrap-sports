from asyncio import Semaphore, run
from app.scraper.scraper_adidas import Adidas
from app.scraper.scraper_nike import Nike
from app.settings import MAX_CONCURRENCY

concurrency_limit = Semaphore(MAX_CONCURRENCY)

def user_input() -> str:
    option = input("[N]Nike [A]Adidas: ").lower()
    while(option not in ["a", "n"]):
        option = input("[N]Nike [A]Adidas: ").lower()
    return option


if __name__ == "__main__":
    try:
        result = user_input()
        if result == "n":
            run(Nike.exec(concurrency_limit))
        else:
            run(Adidas.exec(concurrency_limit))
    except Exception as e:
        print("error", e)