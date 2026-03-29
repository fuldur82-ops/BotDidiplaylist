from urllib.parse import urlparse

ALLOWED_YOUTUBE_HOSTS = {"www.youtube.com", "youtube.com", "youtu.be", "music.youtube.com"}
ALLOWED_SPOTIFY_HOSTS = {"open.spotify.com"}
ALLOWED_DEEZER_HOSTS = {"www.deezer.com", "deezer.com"}
ALLOWED_AMAZON_HOSTS = {"music.amazon.com", "music.amazon.fr", "music.amazon.co.uk",
                        "music.amazon.de", "music.amazon.es", "music.amazon.it"}

MAX_QUEUE_SIZE = 100
MAX_PLAYLIST_SIZE = 100
MAX_SEARCH_LENGTH = 200


def is_valid_youtube_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and parsed.hostname in ALLOWED_YOUTUBE_HOSTS
    except Exception:
        return False


def is_valid_spotify_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and parsed.hostname in ALLOWED_SPOTIFY_HOSTS
    except Exception:
        return False


def is_valid_deezer_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and parsed.hostname in ALLOWED_DEEZER_HOSTS
    except Exception:
        return False


def is_valid_amazon_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and parsed.hostname in ALLOWED_AMAZON_HOSTS
    except Exception:
        return False


def sanitize_search_query(query: str) -> str:
    """Tronque et nettoie une recherche utilisateur."""
    return query.strip()[:MAX_SEARCH_LENGTH]
