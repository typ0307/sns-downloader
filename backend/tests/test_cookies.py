import os
import stat

import pytest

from app.errors import AppError
from app.services.cookies import CookieFile, validate_netscape_cookies

VALID = (
    "# Netscape HTTP Cookie File\n"
    ".instagram.com\tTRUE\t/\tFALSE\t2147483647\tcsrftoken\tabc123\n"
    ".instagram.com\tTRUE\t/\tTRUE\t2147483647\tsessionid\tdef456\n"
)


def test_validate_valid_netscape():
    assert validate_netscape_cookies(VALID) is True


def test_validate_comments_and_blanks_only():
    assert validate_netscape_cookies("# comment only\n\n") is True


def test_validate_rejects_bad_columns():
    assert validate_netscape_cookies("only-three\tcolumns\there\n") is False


def test_cookie_file_creates_0600_and_deletes():
    with CookieFile(VALID.encode("utf-8")) as path:
        assert os.path.exists(path)
        mode = stat.S_IMODE(os.stat(path).st_mode)
        assert mode == 0o600
    assert not os.path.exists(path)


def test_cookie_file_rejects_invalid():
    with pytest.raises(AppError):
        with CookieFile(b"not a cookie file\n"):
            pass


def test_cookie_file_rejects_non_utf8():
    with pytest.raises(AppError):
        with CookieFile(b"\xff\xfe\x00\x01"):
            pass
