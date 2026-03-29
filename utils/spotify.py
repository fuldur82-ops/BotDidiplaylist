import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os


def get_spotify_client():
    return spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        )
    )


def search_track(query: str) -> dict | None:
    """Recherche un titre sur Spotify, retourne nom + artiste."""
    sp = get_spotify_client()
    results = sp.search(q=query, type="track", limit=1)
    tracks = results.get("tracks", {}).get("items", [])
    if not tracks:
        return None
    track = tracks[0]
    return {
        "title": track["name"],
        "artist": track["artists"][0]["name"],
        "query": f"{track['artists'][0]['name']} - {track['name']}",
        "duration_ms": track["duration_ms"],
        "thumbnail": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
    }


def get_playlist_tracks(playlist_url: str) -> list[dict]:
    """Récupère tous les titres d'une playlist Spotify publique."""
    sp = get_spotify_client()
    playlist_id = playlist_url.split("/playlist/")[-1].split("?")[0]
    results = sp.playlist_tracks(playlist_id)
    tracks = []
    while results:
        for item in results.get("items", []):
            track = item.get("track")
            if track:
                tracks.append({
                    "title": track["name"],
                    "artist": track["artists"][0]["name"],
                    "query": f"{track['artists'][0]['name']} - {track['name']}",
                })
        results = sp.next(results) if results.get("next") else None
    return tracks
