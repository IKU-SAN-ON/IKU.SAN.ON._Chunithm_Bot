import json
import os

import aiohttp
from exceptions.song_sync_exceptions import SyncFailException

SONG_SOURCE_URL = os.getenv("SONG_SOURCE_URL")
_WEB_API_BASE = (os.getenv("WEB_API_URL_BASE") or "http://web:3000").rstrip("/")
WEB_API_URL_BASE = (
    _WEB_API_BASE
    if _WEB_API_BASE.endswith("/api/v1")
    else f"{_WEB_API_BASE}/api/v1"
)
TIMEOUT = aiohttp.ClientTimeout(total=300, connect=10)


async def sync_songs() -> None:
    """Pull the full song JSON from SONG_SOURCE_URL and POST it to web."""
    if not SONG_SOURCE_URL:
        raise SyncFailException("SONG_SOURCE_URL is not set.")

    try:
        async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
            async with session.get(SONG_SOURCE_URL) as source:
                if source.status != 200:
                    raise SyncFailException(
                        f"Song source returned HTTP {source.status}."
                    )
                payload = await source.read()

            try:
                songs = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise SyncFailException(
                    "Song source did not return valid JSON."
                ) from exc
            if not isinstance(songs, list) or not songs:
                raise SyncFailException(
                    "Song source returned an empty or non-list payload."
                )

            async with session.post(
                f"{WEB_API_URL_BASE}/internal/updatesongs",
                data=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                body = await response.text()
                if response.status != 200:
                    raise SyncFailException(
                        f"Web API returned HTTP {response.status}: {body[:200]}"
                    )

                try:
                    result = json.loads(body)
                except json.JSONDecodeError as exc:
                    raise SyncFailException("Web API returned invalid JSON.") from exc
                if not result.get("success"):
                    raise SyncFailException(
                        "Web API rejected the song sync: "
                        f"{result.get('error', 'unknown error')}"
                    )
    except (aiohttp.ClientError, TimeoutError) as exc:
        raise SyncFailException(f"Song sync request failed: {exc}") from exc
