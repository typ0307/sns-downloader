from __future__ import annotations

from urllib.parse import urlparse

INSTAGRAM_HOSTS = {"instagram.com", "www.instagram.com"}
X_HOSTS = {
    "x.com",
    "www.x.com",
    "twitter.com",
    "www.twitter.com",
    "mobile.twitter.com",
    "mobile.x.com",
}


def detect_platform(url: str) -> str | None:
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return None

    if parsed.scheme not in ("http", "https"):
        return None

    host = (parsed.hostname or "").lower()
    if host in INSTAGRAM_HOSTS:
        return "instagram"
    if host in X_HOSTS:
        return "x"
    return None


def is_supported_url(url: str) -> bool:
    return detect_platform(url) is not None


def is_instagram_story_url(url: str) -> bool:
    if detect_platform(url) != "instagram":
        return False
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    return parsed.path.startswith("/stories/")
