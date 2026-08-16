from __future__ import annotations

import os
import tempfile
from pathlib import Path

from app.errors import INVALID_COOKIE_FILE, AppError


def validate_netscape_cookies(content: str) -> bool:
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 7:
            return False
    return True


class CookieFile:
    def __init__(self, content: bytes):
        self.content = content
        self._tmp = None
        self.path: str | None = None

    def __enter__(self) -> str:
        try:
            text = self.content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AppError(
                INVALID_COOKIE_FILE,
                "cookies.txt must be UTF-8 encoded.",
            ) from exc

        if not validate_netscape_cookies(text):
            raise AppError(
                INVALID_COOKIE_FILE,
                "Invalid Netscape-format cookies.txt.",
            )

        self._tmp = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".txt",
            prefix="sns-cookies-",
            delete=False,
        )
        self._tmp.write(text)
        self._tmp.flush()
        os.chmod(self._tmp.name, 0o600)
        self.path = self._tmp.name
        return self.path

    def __exit__(self, *exc_info) -> None:
        if self._tmp is not None:
            try:
                self._tmp.close()
            except OSError:
                pass
        if self.path:
            try:
                Path(self.path).unlink(missing_ok=True)
            except OSError:
                pass
        return None
