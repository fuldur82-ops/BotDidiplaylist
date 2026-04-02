import os
import time
import aiohttp

SPOTIFY_API = "https://api.spotify.com/v1"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
DEEZER_API = "https://api.deezer.com"

_token: str | None = None
_token_expires: float = 0.0


async def _get_token() -> str | None:
    global _token, _token_expires
    if _token and time.time() < _token_expires - 30:
        return _token

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None

    async with aiohttp.ClientSession() as session:
        async with session.post(
            SPOTIFY_TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=aiohttp.BasicAuth(client_id, client_secret),
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

    _token = data.get("access_token")
    _token_expires = time.time() + data.get("expires_in", 3600)
    return _token


async def search_track(query: str) -> dict | None:
    """Recherche un titre via l'API Spotify."""
    token = await _get_token()
    if not token:
        return await _deezer_fallback(query)

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{SPOTIFY_API}/search",
            params={"q": query, "type": "track", "limit": 1},
            headers={"Authorization": f"Bearer {token}"},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                return await _deezer_fallback(query)
            data = await resp.json()

    items = data.get("tracks", {}).get("items", [])
    if not items:
        return None

    track = items[0]
    artist = track["artists"][0]["name"] if track.get("artists") else ""
    title = track.get("name", "")
    return {
        "title": title,
        "artist": artist,
        "query": f"{artist} - {title}",
        "duration_ms": track.get("duration_ms", 0),
        "thumbnail": (track.get("album", {}).get("images") or [{}])[0].get("url"),
    }


async def get_playlist_tracks(playlist_url: str) -> list[dict]:
    """Récupère les titres d'une playlist Spotify."""
    # Extrait l'ID de playlist depuis l'URL
    playlist_id = playlist_url.rstrip("/").split("/")[-1].split("?")[0]

    token = await _get_token()
    if not token:
        return []

    tracks = []
    url = f"{SPOTIFY_API}/playlists/{playlist_id}/tracks"
    params = {"limit": 100, "fields": "items(track(name,artists)),next"}

    async with aiohttp.ClientSession() as session:
        while url:
            async with session.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    break
                data = await resp.json()

            for item in data.get("items", []):
                track = item.get("track")
                if not track:
                    continue
                artist = track["artists"][0]["name"] if track.get("artists") else ""
                title = track.get("name", "")
                if artist and title:
                    tracks.append({
                        "title": f"{artist} - {title}",
                        "artist": artist,
                        "query": f"{artist} - {title}",
                    })

            url = data.get("next")
            params = {}  # next URL inclut déjà les params

    return tracks


async def get_deezer_playlist_tracks(playlist_url: str) -> list[dict]:
    """Récupère les titres d'une playlist Deezer."""
    import re
    m = re.search(r"/playlist/(\d+)", playlist_url)
    if not m:
        return []
    playlist_id = m.group(1)

    tracks = []
    url = f"{DEEZER_API}/playlist/{playlist_id}/tracks"
    params = {"limit": 100, "index": 0}

    async with aiohttp.ClientSession() as session:
        while url:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
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

            next_url = data.get("next")
            if next_url:
                url = next_url
                params = {}
            else:
                break

    return tracks


async def _deezer_fallback(query: str) -> dict | None:
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
