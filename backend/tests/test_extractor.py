from pathlib import Path

from app.services.extractor import Extractor
from app.services.storage import LocalStorage


def _extractor():
    return Extractor.__new__(Extractor)


def test_classify():
    ex = _extractor()
    assert ex._classify("mp4") == "video"
    assert ex._classify("m4a") == "audio"
    assert ex._classify("jpg") == "image"


def test_guess_ext():
    ex = _extractor()
    assert ex._guess_ext("https://cdn.example.com/abc.jpg?x=1") == "jpg"
    assert ex._guess_ext("https://cdn.example.com/video.mp4") == "mp4"
    assert ex._guess_ext("https://cdn.example.com/noext") == ""


def test_best_thumbnail_prefers_orig():
    ex = _extractor()
    thumbs = [
        {"id": "small", "url": "http://x/s.jpg", "width": 150, "height": 150},
        {"id": "orig", "url": "http://x/o.jpg", "width": 1000, "height": 1000},
    ]
    assert ex._best_thumbnail(thumbs)["url"] == "http://x/o.jpg"


def test_best_thumbnail_largest_area():
    ex = _extractor()
    thumbs = [
        {"url": "http://x/s.jpg", "width": 150, "height": 150},
        {"url": "http://x/l.jpg", "width": 1080, "height": 1350},
    ]
    assert ex._best_thumbnail(thumbs)["url"] == "http://x/l.jpg"


def test_best_thumbnail_numeric_id_without_dimensions():
    ex = _extractor()
    thumbs = [
        {"id": "0", "url": "http://x/0.jpg"},
        {"id": "7", "url": "http://x/7.jpg"},
        {"id": "13", "url": "http://x/13.jpg"},
    ]
    assert ex._best_thumbnail(thumbs)["url"] == "http://x/13.jpg"


def test_clean_strips_ansi_and_error_prefix():
    ex = _extractor()
    assert ex._clean("\x1b[0;31mERROR:\x1b[0m [x] message") == "[x] message"


class _FakeYDL:
    def __init__(self, tmpdir: Path):
        self.tmpdir = tmpdir
        self.calls = []

    def process_video_result(self, entry, download=True):
        self.calls.append(dict(entry))
        ext = entry.get("ext") or ("mp4" if entry.get("formats") else "jpg")
        (self.tmpdir / f"{entry['id']}.{ext}").write_bytes(b"x")


def test_download_and_collect(tmp_path):
    storage = LocalStorage(tmp_path)
    ex = Extractor(storage)
    workdir = Path(tmp_path) / "work"
    workdir.mkdir()
    fake = _FakeYDL(workdir)

    info = {
        "title": "post",
        "entries": [
            {"id": "vid123", "formats": [{"url": "https://x/v.mp4", "ext": "mp4"}]},
            {"id": "img1", "thumbnails": [{"url": "https://x/i.jpg", "width": 1080, "height": 1080}]},
        ],
    }

    ex._download(fake, info)
    media = ex._collect(workdir, info, "job-abcdef123456")

    assert fake.calls[0]["id"] == "vid123"
    assert fake.calls[1]["url"] == "https://x/i.jpg"
    assert fake.calls[1]["ext"] == "jpg"

    assert len(media) == 2
    assert media[0]["type"] == "video"
    assert media[1]["type"] == "image"
    assert media[1]["ext"] == "jpg"
    with storage.open(media[1]["id"]) as f:
        assert f.read() == b"x"
