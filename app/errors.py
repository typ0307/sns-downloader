from __future__ import annotations

UNSUPPORTED_URL = "UNSUPPORTED_URL"
EXTRACT_FAILED = "EXTRACT_FAILED"
LOGIN_REQUIRED = "LOGIN_REQUIRED"
RATE_LIMITED = "RATE_LIMITED"
MEDIA_NOT_FOUND = "MEDIA_NOT_FOUND"
INVALID_COOKIE_FILE = "INVALID_COOKIE_FILE"


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)
