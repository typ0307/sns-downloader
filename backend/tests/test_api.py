import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client(tmp_path):
    from app.services.storage import LocalStorage

    app.state.storage = LocalStorage(tmp_path)
    with TestClient(app) as c:
        yield c


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_extract_unsupported_url(client):
    res = client.post("/api/extract", data={"url": "https://example.com/p/1"})
    assert res.status_code == 400
    body = res.json()
    assert body["error"]["code"] == "UNSUPPORTED_URL"


def test_extract_invalid_cookie_file(client):
    res = client.post(
        "/api/extract",
        data={"url": "https://www.instagram.com/p/ABC/"},
        files={"cookie_file": ("cookies.txt", b"not a cookie", "text/plain")},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_COOKIE_FILE"


def test_download_not_found(client):
    res = client.get("/api/download/nope.mp4")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "MEDIA_NOT_FOUND"
