import yt_dlp
import asyncio

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "opus",
    }],
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


async def search_youtube(query: str) -> dict | None:
    """Recherche un titre sur YouTube et retourne l'URL audio."""
    opts = {**YDL_OPTIONS, "noplaylist": True}
    loop = asyncio.get_event_loop()

    def _search():
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            entries = info.get("entries", [])
            if not entries:
                return None
            entry = entries[0]
            return {
                "url": entry["url"],
                "title": entry.get("title", query),
                "duration": entry.get("duration", 0),
                "webpage_url": entry.get("webpage_url", ""),
                "thumbnail": entry.get("thumbnail", ""),
            }

    return await loop.run_in_executor(None, _search)


async def get_playlist(url: str) -> list[dict]:
    """Extrait tous les titres d'une playlist YouTube."""
    opts = {**YDL_OPTIONS, "noplaylist": False, "extract_flat": True}
    loop = asyncio.get_event_loop()

    def _get():
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            entries = info.get("entries", [])
            return [
                {
                    "title": e.get("title", "Titre inconnu"),
                    "url": e.get("url") or e.get("webpage_url", ""),
                    "duration": e.get("duration", 0),
                    "thumbnail": e.get("thumbnail", ""),
                    "is_url": True,
                }
                for e in entries if e
            ]

    return await loop.run_in_executor(None, _get)


async def resolve_url(url: str) -> dict | None:
    """Résout une URL YouTube directe en flux audio."""
    opts = {**YDL_OPTIONS, "noplaylist": True}
    loop = asyncio.get_event_loop()

    def _resolve():
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "url": info["url"],
                "title": info.get("title", url),
                "duration": info.get("duration", 0),
                "webpage_url": info.get("webpage_url", url),
                "thumbnail": info.get("thumbnail", ""),
            }

    return await loop.run_in_executor(None, _resolve)


def format_duration(seconds: int) -> str:
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
