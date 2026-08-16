from io import BytesIO

import pytest

from app.services.storage import LocalStorage


def test_save_open_size(tmp_path):
    storage = LocalStorage(tmp_path)
    media_id = "abc123.mp4"
    storage.save(BytesIO(b"hello world"), media_id)
    assert storage.size(media_id) == 11
    with storage.open(media_id) as f:
        assert f.read() == b"hello world"


def test_rejects_traversal(tmp_path):
    storage = LocalStorage(tmp_path)
    with pytest.raises(ValueError):
        storage.open("../etc/passwd")
    with pytest.raises(ValueError):
        storage.save(BytesIO(b"x"), "sub/dir/file.mp4")
