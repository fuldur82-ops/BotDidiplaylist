import aiohttp


DEEZER_API = "https://api.deezer.com"


async def search_track(query: str) -> dict | None:
    """Recherche un titre via l'API Deezer (gratuite, sans clé API)."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{DEEZER_API}/search",
            params={"q": query, "limit": 1},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

    tracks = data.get("data", [])
    if not tracks:
        return None

    track = tracks[0]
    artist = track.get("artist", {}).get("name", "")
    title = track.get("title", "")
    return {
        "title": title,
        "artist": artist,
        "query": f"{artist} - {title}",
        "duration_ms": track.get("duration", 0) * 1000,
        "thumbnail": track.get("album", {}).get("cover_medium"),
    }


async def get_playlist_tracks(playlist_url: str) -> list[dict]:
    """Récupère les titres d'une playlist Deezer publique."""
    playlist_id = playlist_url.rstrip("/").split("/")[-1].split("?")[0]
    tracks = []
    url = f"{DEEZER_API}/playlist/{playlist_id}/tracks"

    async with aiohttp.ClientSession() as session:
        while url:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    break
                data = await resp.json()

            for item in data.get("data", []):
                artist = item.get("artist", {}).get("name", "")
                title = item.get("title", "")
                if artist and title:
                    tracks.append({
                        "title": f"{artist} - {title}",
                        "artist": artist,
                        "query": f"{artist} - {title}",
                    })

            url = data.get("next")

    return tracks
