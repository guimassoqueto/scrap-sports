from abc import ABC, abstractmethod
from asyncio import Semaphore

class Scraper(ABC):
    @abstractmethod
    async def scrap(self, url: str, concurrency_limit: Semaphore) -> None:
        pass
