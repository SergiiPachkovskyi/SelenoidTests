from typing import Any, Dict

from fastapi import APIRouter

from scraper import SelenoidWebScraper

router = APIRouter(tags=["main"], prefix="/api/v1.0")


@router.get("")
async def greeting() -> Dict[str, Any]:
    print("Greeting endpoint accessed")
    scraper = SelenoidWebScraper()
    scraper.scrape("https://www.pravda.com.ua/rus/news/2023/11/23/7430013/")
    return {"HI!": "I`m ScraperAPI and I am working with Selenoid!"}
