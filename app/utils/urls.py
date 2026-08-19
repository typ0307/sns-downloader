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

# yt-dlp PinterestIE._VALID_URL_BASE regional/country TLDs
PINTEREST_HOSTS = frozenset(
    f"pinterest.{tld}"
    for tld in {
        "com", "fr", "de", "ch", "jp", "cl", "ca", "it", "co.uk", "nz", "ru",
        "com.au", "at", "pt", "co.kr", "es", "com.mx", "dk", "ph", "th",
        "com.uy", "co", "nl", "info", "kr", "ie", "vn", "com.vn", "ec", "mx",
        "in", "pe", "co.at", "hu", "co.in", "co.nz", "id", "com.ec", "com.py",
        "tw", "be", "uk", "com.bo", "com.pe",
    }
)


def _is_pinterest_host(host: str) -> bool:
    return any(host == base or host.endswith(f".{base}") for base in PINTEREST_HOSTS)


def _is_valid_http_url(url: str) -> tuple[bool, str | None]:
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False, None
    if parsed.scheme not in ("http", "https"):
        return False, None
    return True, (parsed.hostname or "").lower()


def detect_platform(url: str) -> str | None:
    valid, host = _is_valid_http_url(url)
    if not valid:
        return None
    if host in INSTAGRAM_HOSTS:
        return "instagram"
    if host in X_HOSTS:
        return "x"
    if _is_pinterest_host(host):
        return "pinterest" if is_pinterest_pin_url(url) else None
    return None


def is_supported_url(url: str) -> bool:
    return detect_platform(url) is not None


def is_pinterest_pin_url(url: str) -> bool:
    valid, host = _is_valid_http_url(url)
    if not valid or not _is_pinterest_host(host):
        return False
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    return parsed.path.startswith("/pin/")


def is_instagram_story_url(url: str) -> bool:
    if detect_platform(url) != "instagram":
        return False
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    return parsed.path.startswith("/stories/")
