import aiohttp
from bs4 import BeautifulSoup
from utils.validators import is_valid_amazon_url


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
}


async def get_amazon_playlist_tracks(url: str) -> list[dict]:
    """
    Tente de scraper une playlist Amazon Music publique.
    Retourne une liste de {'title': ..., 'artist': ..., 'query': ...}
    pour ensuite chercher sur YouTube.

    ⚠️ Fragile — Amazon peut bloquer le scraping ou changer sa structure HTML.
    """
    if not is_valid_amazon_url(url):
        return []

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")
        tracks = []

        # Amazon Music structure — peut changer
        for row in soup.select("[class*='MusicLibrary'] [class*='row'], [data-testid='track-row']"):
            title_el = row.select_one("[class*='title'], [data-testid='track-name']")
            artist_el = row.select_one("[class*='artist'], [data-testid='artist-name']")
            if title_el:
                title = title_el.get_text(strip=True)
                artist = artist_el.get_text(strip=True) if artist_el else ""
                tracks.append({
                    "title": title,
                    "artist": artist,
                    "query": f"{artist} - {title}" if artist else title,
                })

        return tracks

    except Exception:
        return []


def is_amazon_url(url: str) -> bool:
    return is_valid_amazon_url(url)
