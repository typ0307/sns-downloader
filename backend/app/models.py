from __future__ import annotations

from pydantic import BaseModel


class MediaItem(BaseModel):
    id: str
    type: str
    ext: str
    size_bytes: int
    download_url: str
    direct_url: str | None = None


class ExtractResponse(BaseModel):
    id: str
    platform: str
    title: str
    media: list[MediaItem]


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str
