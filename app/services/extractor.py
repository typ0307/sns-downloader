from __future__ import annotations

import json
import math
import re
import secrets
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from yt_dlp.cookies import CookieLoadError
from yt_dlp.extractor.instagram import InstagramStoryIE
from yt_dlp.jsinterp import js_number_to_string
from yt_dlp.networking import Request
from yt_dlp.networking.exceptions import HTTPError
from yt_dlp.utils import (
    DownloadError,
    ExtractorError,
    UnsupportedError,
    traverse_obj,
)

from app.errors import EXTRACT_FAILED, LOGIN_REQUIRED, RATE_LIMITED, AppError
from app.services.storage import LocalStorage
from app.utils.urls import is_instagram_story_url

VIDEO_EXTS = {"mp4", "mov", "webm", "m4v", "mkv", "avi"}
AUDIO_EXTS = {"m4a", "mp3", "aac", "opus", "wav", "flac", "ogg"}
_MANIFEST_PROTOCOLS = {"m3u8", "m3u8_native", "http_dash_segments", "ism", "f4m"}

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_TWID_RE = re.compile(r"status/(\d+)")
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

_OG_META_RE = (
    r'<meta[^>]*property=["\']%s["\'][^>]*content=["\']([^"\']+)["\']',
    r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']%s["\']',
)


def _extract_og_meta(html: str, prop: str) -> str | None:
    for pattern in _OG_META_RE:
        match = re.search(pattern % re.escape(prop), html, re.IGNORECASE)
        if match:
            return match.group(1).replace("&amp;", "&")
    return None


class _ErrorLogger:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def debug(self, _msg: str) -> None:
        pass

    def warning(self, _msg: str) -> None:
        pass

    def error(self, msg: str) -> None:
        self.errors.append(msg)


class Extractor:
    def __init__(
        self,
        storage: LocalStorage,
        cookies_from_browser: str | None = None,
    ):
        self.storage = storage
        self.cookies_from_browser = cookies_from_browser

    def extract(self, url: str, platform: str, cookiefile: str | None) -> dict:
        if (
            platform == "instagram"
            and is_instagram_story_url(url)
            and not cookiefile
            and not self.cookies_from_browser
        ):
            raise AppError(
                LOGIN_REQUIRED,
                "Instagram stories require login. Please upload a valid cookies.txt or enable browser session.",
                401,
            )

        job_id = f"job-{uuid.uuid4()}"
        title = ""
        media: list[dict] = []
        logger = _ErrorLogger()
        is_story = platform == "instagram" and is_instagram_story_url(url)

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
                "logger": logger,
            }
            if cookiefile:
                opts["cookiefile"] = cookiefile
            elif self.cookies_from_browser:
                opts["cookiesfrombrowser"] = (self.cookies_from_browser,)

            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    if is_story:
                        title, media = self._extract_instagram_story(ydl, url, job_id)
                    elif platform == "pinterest":
                        title, media = self._extract_pinterest(ydl, url, job_id, tmpdir)
                    else:
                        info = ydl.extract_info(url, download=False)
                        title = self._extract_title(info)
                        self._download(ydl, info)
                        media = self._collect(tmpdir, info, job_id)
                        if platform == "x":
                            self._download_x_photos(ydl, url, job_id, media)
            except UnsupportedError as exc:
                raise AppError(EXTRACT_FAILED, self._clean(str(exc)), 400) from exc
            except CookieLoadError as exc:
                raise AppError(
                    LOGIN_REQUIRED,
                    "Failed to load cookies from the browser session. Unlock your browser or upload a valid cookies.txt instead.",
                    401,
                ) from exc
            except (DownloadError, ExtractorError) as exc:
                raise self._map_error(exc) from exc

        if not media:
            message = self._first_error(logger.errors)
            if message:
                raise self._map_message(message)
            if platform == "instagram" and is_instagram_story_url(url):
                raise AppError(
                    EXTRACT_FAILED,
                    "No media found. This Instagram story has expired or is no longer available.",
                    502,
                )
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
            media.append(self._media_dict(media_id, self._classify(ext), ext, self._direct_url(entry)))
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

    def _media_dict(self, media_id: str, media_type: str, ext: str, direct_url: str | None = None) -> dict:
        return {
            "id": media_id,
            "type": media_type,
            "ext": ext,
            "size_bytes": self.storage.size(media_id),
            "download_url": f"/api/download/{media_id}",
            "direct_url": direct_url,
        }

    def _direct_url(self, entry: dict | None) -> str | None:
        if not entry:
            return None
        if entry.get("url"):
            return entry["url"]
        combined = [
            f for f in (entry.get("formats") or [])
            if f.get("url")
            and f.get("acodec") != "none"
            and f.get("vcodec") != "none"
            and f.get("protocol") not in _MANIFEST_PROTOCOLS
        ]
        if combined:
            best = max(
                combined,
                key=lambda f: (f.get("height") or 0, f.get("width") or 0, f.get("tbr") or 0),
            )
            return best["url"]
        return None

    def _extract_title(self, info: dict | None) -> str:
        if not info:
            return ""
        value = info.get("title") or info.get("description") or ""
        return value.strip()[:500]

    def _download_x_photos(self, ydl, url: str, job_id: str, media: list[dict]) -> None:
        twid = self._extract_twid(url)
        if not twid:
            return
        try:
            details = self._fetch_x_media_details(ydl, twid)
        except Exception:
            return
        for detail in details or []:
            if detail.get("type") != "photo":
                continue
            photo_url = self._photo_url(detail)
            if not photo_url:
                continue
            ext = self._guess_ext(photo_url) or "jpg"
            media_id = self._new_media_id(job_id, len(media), ext)
            try:
                with ydl.urlopen(photo_url) as resp:
                    self.storage.save(resp, media_id)
            except Exception:
                continue
            media.append(self._media_dict(media_id, "image", ext, photo_url))

    def _extract_pinterest(self, ydl, url: str, job_id: str, tmpdir: Path) -> tuple[str, list[dict]]:
        try:
            info = ydl.extract_info(url, download=False)
            title = self._extract_title(info)
            self._download(ydl, info)
            media = self._collect(tmpdir, info, job_id)
            if media:
                return title, media
        except Exception:
            pass
        return self._extract_pinterest_og_image(ydl, url, job_id)

    def _extract_pinterest_og_image(self, ydl, url: str, job_id: str) -> tuple[str, list[dict]]:
        match = re.search(r"/pin/(?:[\w-]+--)?(\d+)", url)
        pin_id = match.group(1) if match else None
        try:
            page = ydl.urlopen(url).read().decode("utf-8", "replace")
            image_url = None
            for prop in ("og:image", "og:image:url"):
                candidate = _extract_og_meta(page, prop)
                if candidate:
                    image_url = candidate
                    break
            if not image_url:
                return "", []
            title = _extract_og_meta(page, "og:title")
            if not title:
                title = f"Pinterest pin {pin_id}" if pin_id else "Pinterest pin"
            ext = self._guess_ext(image_url) or "jpg"
            media_id = self._new_media_id(job_id, 0, ext)
            with ydl.urlopen(image_url) as resp:
                self.storage.save(resp, media_id)
            media = [self._media_dict(media_id, self._classify(ext), ext, image_url)]
            return title, media
        except Exception:
            return "", []

    def _extract_twid(self, url: str) -> str | None:
        match = _TWID_RE.search(url)
        return match.group(1) if match else None

    def _extract_instagram_story(self, ydl, url: str, job_id: str) -> tuple[str, list[dict]]:
        ie = InstagramStoryIE(ydl)
        match = ie._match_valid_url(url)
        if not match:
            return "", []
        username, story_id = match.group("user", "id")
        title = f"Story by {username}"
        display_id = story_id or username

        try:
            page = ydl.urlopen(url).read().decode("utf-8", "replace")
        except Exception:
            return title, []
        user_info = ie._search_json(r'"user":', page, "user info", display_id, fatal=False)
        if not user_info:
            return title, []
        user_id = traverse_obj(user_info, "pk", "id", expected_type=str)
        if not user_id:
            return title, []

        try:
            resp = ydl.urlopen(Request(
                f"{ie._API_BASE_URL}/feed/reels_media/?reel_ids={user_id}",
                headers=ie._api_headers,
            ))
            data = json.loads(resp.read().decode("utf-8", "replace"))
        except HTTPError as exc:
            raise self._map_api_status(exc.status) from exc
        except Exception:
            return title, []

        items = traverse_obj(
            (data or {}).get("reels") or {},
            (f"highlight:{story_id}", "items"),
            (user_id, "items"),
        ) or []

        media: list[dict] = []
        index = 0
        for item in items:
            if story_id and username != "highlights":
                item_pk = str(traverse_obj(item, "pk", expected_type=str) or "")
                if item_pk != story_id:
                    continue
            for entry in self._story_entries(ie, item):
                direct_url = self._story_entry_url(entry)
                if not direct_url:
                    continue
                ext = self._guess_ext(direct_url) or "jpg"
                media_id = self._new_media_id(job_id, index, ext)
                index += 1
                try:
                    with ydl.urlopen(direct_url) as media_resp:
                        self.storage.save(media_resp, media_id)
                except Exception:
                    continue
                media.append(self._media_dict(media_id, self._classify(ext), ext, direct_url))
        return title, media

    def _story_entries(self, ie, item: dict) -> list[dict]:
        product = ie._extract_product(item)
        if product.get("_type") == "playlist":
            return product.get("entries") or []
        return [product]

    def _story_entry_url(self, entry: dict) -> str | None:
        formats = entry.get("formats") or []
        if formats:
            best = max(
                formats,
                key=lambda f: (f.get("height") or 0, f.get("width") or 0, f.get("tbr") or 0),
            )
            return best.get("url")
        thumb = self._best_thumbnail(entry.get("thumbnails"))
        return thumb.get("url") if thumb else None

    def _map_api_status(self, status: int) -> AppError:
        if status in (401, 403):
            return AppError(
                LOGIN_REQUIRED,
                "Failed to authenticate with Instagram. Check your cookies or browser session.",
                401,
            )
        if status == 429:
            return AppError(
                RATE_LIMITED,
                "Rate limited by Instagram. Please try again later.",
                429,
            )
        return AppError(EXTRACT_FAILED, f"Instagram API returned status {status}.", 502)

    def _fetch_x_media_details(self, ydl, twid: str) -> list[dict]:
        token = js_number_to_string((int(twid) / 1e15) * math.pi, 36).translate(
            str.maketrans(dict.fromkeys("0."))
        )
        endpoint = f"https://cdn.syndication.twimg.com/tweet-result?id={twid}&token={token}"
        req = Request(endpoint, headers={"User-Agent": "Googlebot"})
        with ydl.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        return data.get("mediaDetails") or []

    def _photo_url(self, detail: dict) -> str | None:
        base = detail.get("media_url_https") or detail.get("media_url")
        if not base:
            return None
        sizes = detail.get("sizes") or {}
        name = next((n for n in ("orig", "large", "medium") if n in sizes), None)
        if name:
            sep = "&" if "?" in base else "?"
            return f"{base}{sep}name={name}"
        return base

    def _map_error(self, exc: Exception) -> AppError:
        return self._map_message(self._clean(str(exc)))

    def _map_message(self, message: str) -> AppError:
        msg = message.lower()
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
        return AppError(EXTRACT_FAILED, message[:500] or "Extraction failed.", 502)

    def _first_error(self, errors: list[str]) -> str | None:
        for error in errors:
            cleaned = self._clean(error)
            if cleaned:
                return cleaned
        return None

    def _clean(self, value: str) -> str:
        return _ANSI_RE.sub("", value).replace("ERROR:", "").strip()
