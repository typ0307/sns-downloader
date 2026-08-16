import pytest

from app.utils.urls import detect_platform, is_supported_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.instagram.com/p/ABC123/", "instagram"),
        ("https://instagram.com/reel/DEF456/", "instagram"),
        ("http://instagram.com/p/ABC/", "instagram"),
        ("https://x.com/user/status/123", "x"),
        ("https://twitter.com/user/status/123", "x"),
        ("https://mobile.twitter.com/user/status/123", "x"),
        ("https://www.x.com/user/status/123", "x"),
    ],
)
def test_detect_platform_supported(url, expected):
    assert detect_platform(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "https://evilinstagram.com/p/ABC/",
        "https://instagram.com.evil.com/p/ABC/",
        "https://example.com/p/ABC/",
        "https://youtube.com/watch?v=abc",
        "ftp://instagram.com/p/ABC/",
        "not-a-url",
        "",
        "instagram.com/p/ABC/",
        "https://sub.instagram.com/p/ABC/",
    ],
)
def test_detect_platform_rejects(url):
    assert detect_platform(url) is None


def test_is_supported_url():
    assert is_supported_url("https://www.instagram.com/p/ABC/") is True
    assert is_supported_url("https://example.com") is False
