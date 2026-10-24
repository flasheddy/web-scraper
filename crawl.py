from urllib.parse import urlsplit


def normalize_url(url: str) -> str:
    parsed = urlsplit(url)
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/")
    return netloc + path
