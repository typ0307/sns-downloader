from __future__ import annotations

import shutil
from pathlib import Path
from typing import BinaryIO


class LocalStorage:
    def __init__(self, base_dir: str | Path):
        self.media_dir = Path(base_dir) / "media"
        self.media_dir.mkdir(parents=True, exist_ok=True)

    def save(self, stream, media_id: str) -> str:
        dest = self._safe_path(media_id)
        with dest.open("wb") as f:
            shutil.copyfileobj(stream, f)
        return media_id

    def open(self, media_id: str) -> BinaryIO:
        return self._safe_path(media_id).open("rb")

    def size(self, media_id: str) -> int:
        return self._safe_path(media_id).stat().st_size

    def _safe_path(self, media_id: str) -> Path:
        if not media_id or Path(media_id).name != media_id:
            raise ValueError("Invalid media id")
        base = self.media_dir.resolve()
        target = (base / media_id).resolve()
        if target.parent != base:
            raise ValueError("Invalid media id")
        return target
