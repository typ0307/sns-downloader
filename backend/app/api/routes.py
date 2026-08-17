from __future__ import annotations

import mimetypes
from contextlib import ExitStack

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.errors import (
    INVALID_COOKIE_FILE,
    MEDIA_NOT_FOUND,
    UNSUPPORTED_URL,
    AppError,
)
from app.limiter import limiter
from app.models import ExtractResponse, HealthResponse
from app.services.cookies import CookieFile
from app.services.extractor import Extractor
from app.utils.urls import detect_platform

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/extract", response_model=ExtractResponse)
@limiter.limit(lambda: get_settings().rate_limit)
def extract(
    request: Request,
    url: str = Form(...),
    cookie_file: UploadFile | None = File(None),
    browser: str | None = Form(None),
) -> ExtractResponse:
    platform = detect_platform(url)
    if platform is None:
        raise AppError(
            UNSUPPORTED_URL,
            "Unsupported URL. Only Instagram and X (Twitter) links are allowed.",
            400,
        )

    storage = request.app.state.storage
    browser_name = (browser or "").strip() or request.app.state.settings.cookies_from_browser
    extractor = Extractor(storage, cookies_from_browser=browser_name)

    with ExitStack() as stack:
        cookiefile = None
        if cookie_file is not None:
            content = cookie_file.file.read()
            if len(content) > request.app.state.settings.max_upload_bytes:
                raise AppError(
                    INVALID_COOKIE_FILE,
                    "cookies.txt is too large.",
                    413,
                )
            cookiefile = stack.enter_context(CookieFile(content))

        result = extractor.extract(url, platform, cookiefile)

    return ExtractResponse(**result)


@router.get("/download/{media_id}")
def download(request: Request, media_id: str, inline: int = 0) -> StreamingResponse:
    storage = request.app.state.storage
    try:
        stream = storage.open(media_id)
    except (FileNotFoundError, ValueError) as exc:
        raise AppError(MEDIA_NOT_FOUND, "Media not found.", 404) from exc

    ext = media_id.rsplit(".", 1)[-1].lower() if "." in media_id else ""
    content_type = mimetypes.guess_type(media_id)[0] or "application/octet-stream"
    disposition = "inline" if inline else "attachment"
    headers = {"Content-Disposition": f'{disposition}; filename="{media_id}"'}
    return StreamingResponse(stream, media_type=content_type, headers=headers)
