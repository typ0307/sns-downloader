from __future__ import annotations

import re
import secrets
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError, UnsupportedError

from app.errors import EXTRACT_FAILED, LOGIN_REQUIRED, RATE_LIMITED, AppError
from app.services.storage import LocalStorage

VIDEO_EXTS = {"mp4", "mov", "webm", "m4v", "mkv", "avi"}
AUDIO_EXTS = {"m4a", "mp3", "aac", "opus", "wav", "flac", "ogg"}

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_LOGIN_HINTS = (
    "login",
    "log in",
    "sign in",
    "cookie",
    "auth",
    "private",
    "age",
    "restricted",
)
_RATE_HINTS = ("rate limit", "rate-limit", "too many", "429", "throttl")


class Extractor:
    def __init__(self, storage: LocalStorage):
        self.storage = storage

    def extract(self, url: str, platform: str, cookiefile: str | None) -> dict:
        job_id = f"job-{uuid.uuid4()}"
        title = ""
        media: list[dict] = []

        with tempfile.TemporaryDirectory(prefix="sns-") as tmp:
            tmpdir = Path(tmp)
            opts: dict = {
                "outtmpl": str(tmpdir / "%(id)s.%(ext)s"),
                "quiet": True,
                "no_warnings": True,
                "noprogress": True,
                "noplaylist": False,
                "ignoreerrors": True,
                "ignore_no_formats_error": True,
            }
            if cookiefile:
                opts["cookiefile"] = cookiefile

            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = self._extract_title(info)
                    self._download(ydl, info)
                    media = self._collect(tmpdir, info, job_id)
            except UnsupportedError as exc:
                raise AppError(EXTRACT_FAILED, self._clean(str(exc)), 400) from exc
            except (DownloadError, ExtractorError) as exc:
                raise self._map_error(exc) from exc

        if not media:
            raise AppError(EXTRACT_FAILED, "No downloadable media found.", 502)

        return {
            "id": job_id,
            "platform": platform,
            "title": title,
            "media": media,
        }

    def _download(self, ydl, info: dict | None) -> None:
        for entry in self._iter_media(info):
            if not entry:
                continue
            if not entry.get("formats") and not entry.get("url") and entry.get("thumbnails"):
                thumb = self._best_thumbnail(entry["thumbnails"])
                if not thumb or not thumb.get("url"):
                    continue
                entry["url"] = thumb["url"]
                entry["ext"] = self._guess_ext(thumb["url"]) or "jpg"
            try:
                ydl.process_video_result(entry, download=True)
            except Exception:
                continue

    def _collect(self, tmpdir: Path, info: dict | None, job_id: str) -> list[dict]:
        files = self._index_files(tmpdir)
        media: list[dict] = []
        for index, entry in enumerate(self._iter_media(info)):
            if not entry:
                continue
            path = files.get(entry.get("id"))
            if not path:
                continue
            ext = path.suffix.lstrip(".").lower()
            if not ext:
                continue
            media_id = self._new_media_id(job_id, index, ext)
            with path.open("rb") as f:
                self.storage.save(f, media_id)
            media.append(self._media_dict(media_id, self._classify(ext), ext))
        return media

    def _iter_media(self, info: dict | None):
        if not info:
            return
        entries = info.get("entries")
        if entries:
            for entry in entries:
                if entry:
                    yield entry
        else:
            yield info

    def _index_files(self, tmpdir: Path) -> dict[str, Path]:
        index: dict[str, Path] = {}
        for path in tmpdir.iterdir():
            if path.is_file() and path.suffix.lower() not in (".part", ".ytdl"):
                index[path.stem] = path
        return index

    def _best_thumbnail(self, thumbnails) -> dict | None:
        best: dict | None = None
        best_key = (-1, -1)
        for thumb in thumbnails or []:
            if not thumb.get("url"):
                continue
            if thumb.get("id") == "orig":
                return thumb
            area = (thumb.get("width") or 0) * (thumb.get("height") or 0)
            try:
                index = int(thumb.get("id"))
            except (TypeError, ValueError):
                index = 0
            key = (area, index)
            if key > best_key:
                best_key = key
                best = thumb
        return best

    def _classify(self, ext: str) -> str:
        if ext in VIDEO_EXTS:
            return "video"
        if ext in AUDIO_EXTS:
            return "audio"
        return "image"

    def _new_media_id(self, job_id: str, index: int, ext: str) -> str:
        short = job_id.split("-", 1)[-1][:8]
        token = f"{short}-{index:02d}-{secrets.token_hex(4)}"
        return f"{token}.{ext}" if ext else token

    def _guess_ext(self, url: str) -> str:
        path = urlparse(url).path
        if "." not in path:
            return ""
        ext = path.rsplit(".", 1)[-1].lower()
        return ext if 1 <= len(ext) <= 5 else ""

    def _media_dict(self, media_id: str, media_type: str, ext: str) -> dict:
        return {
            "id": media_id,
            "type": media_type,
            "ext": ext,
            "size_bytes": self.storage.size(media_id),
            "download_url": f"/api/download/{media_id}",
        }

    def _extract_title(self, info: dict | None) -> str:
        if not info:
            return ""
        value = info.get("title") or info.get("description") or ""
        return value.strip()[:500]

    def _map_error(self, exc: Exception) -> AppError:
        msg = self._clean(str(exc)).lower()
        if any(hint in msg for hint in _LOGIN_HINTS):
            return AppError(
                LOGIN_REQUIRED,
                "Login required. Please upload a valid cookies.txt.",
                401,
            )
        if any(hint in msg for hint in _RATE_HINTS):
            return AppError(
                RATE_LIMITED,
                "Rate limited by the platform. Please try again later.",
                429,
            )
        return AppError(EXTRACT_FAILED, self._clean(str(exc))[:500] or "Extraction failed.", 502)

    def _clean(self, value: str) -> str:
        return _ANSI_RE.sub("", value).replace("ERROR:", "").strip()
