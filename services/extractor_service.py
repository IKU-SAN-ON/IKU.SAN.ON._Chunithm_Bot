import os

import aiohttp
from exceptions.rating_check_exceptions import RatingCheckError

EXTRACTOR_TIMEOUT = aiohttp.ClientTimeout(total=60, connect=10)
WEB_TIMEOUT = aiohttp.ClientTimeout(total=15, connect=5)


def _web_api_base() -> str:
    base = (os.getenv("WEB_API_URL_BASE") or "http://localhost:3000").rstrip("/")
    return base if base.endswith("/api/v1") else f"{base}/api/v1"


EXTRACTOR_API_URL_BASE = (
    os.getenv("EXTRACTOR_API_URL_BASE") or "http://localhost:8000"
).rstrip("/")
WEB_API_URL_BASE = _web_api_base()


async def extract_rating_from_image(data: aiohttp.FormData) -> dict:
    """Send the image to the extractor API and return the extracted data."""
    try:
        async with (
            aiohttp.ClientSession(timeout=EXTRACTOR_TIMEOUT) as session,
            session.post(f"{EXTRACTOR_API_URL_BASE}/extract", data=data) as resp,
        ):
            if resp.status != 200:
                raise RatingCheckError(
                    message="無法從圖片中提取資料。",
                    details=f"Extractor API returned status {resp.status}",
                )
            return await resp.json()
    except (aiohttp.ClientError, TimeoutError) as exc:
        raise RatingCheckError(
            message="無法連接圖片辨識服務，請稍後再試。",
            details=str(exc),
        ) from exc


async def search_constant(song: str, difficulty: str) -> dict:
    """Search for a song's constant by title and difficulty."""
    try:
        async with (
            aiohttp.ClientSession(timeout=WEB_TIMEOUT) as session,
            session.get(
                f"{WEB_API_URL_BASE}/internal/getsongconst",
                params={"q": song, "diff": difficulty},
            ) as resp,
        ):
            if resp.status != 200:
                raise RatingCheckError(
                    message="無法搜尋定數。",
                    details=f"Web API returned status {resp.status}",
                )
            return await resp.json()
    except (aiohttp.ClientError, TimeoutError) as exc:
        raise RatingCheckError(
            message="無法連接歌曲資料服務，請稍後再試。",
            details=str(exc),
        ) from exc
