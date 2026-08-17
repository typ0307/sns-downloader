import mimetypes
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

import streamlit as st

from app.errors import AppError
from app.services.cookies import CookieFile
from app.services.extractor import Extractor
from app.services.storage import LocalStorage
from app.utils.urls import detect_platform

ERROR_MESSAGES = {
    "UNSUPPORTED_URL": "지원하지 않는 URL입니다. Instagram과 X(Twitter) 링크만 지원합니다.",
    "EXTRACT_FAILED": "미디어 추출에 실패했습니다. 링크를 확인하거나 cookies.txt를 업로드해 보세요.",
    "LOGIN_REQUIRED": "로그인이 필요합니다. 유효한 cookies.txt를 업로드하세요.",
    "RATE_LIMITED": "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.",
    "MEDIA_NOT_FOUND": "미디어를 찾을 수 없습니다.",
    "INVALID_COOKIE_FILE": "cookies.txt 파일 형식이 올바르지 않습니다.",
}


def extract_media(url: str, cookie_bytes: bytes | None):
    platform = detect_platform(url)
    if platform is None:
        raise AppError("UNSUPPORTED_URL", "지원하지 않는 URL입니다.", 400)

    with ExitStack() as stack:
        cookiefile = None
        if cookie_bytes is not None:
            cookiefile = stack.enter_context(CookieFile(cookie_bytes))

        media_dir = stack.enter_context(tempfile.TemporaryDirectory(prefix="sns-"))
        storage = LocalStorage(media_dir)
        result = Extractor(storage).extract(url, platform, cookiefile)

        items = []
        for item in result["media"]:
            path = Path(media_dir) / "media" / item["id"]
            data = path.read_bytes()
            items.append(
                {
                    "id": item["id"],
                    "type": item["type"],
                    "ext": item["ext"],
                    "mime": mimetypes.guess_type(item["id"])[0] or "application/octet-stream",
                    "data": data,
                }
            )
        return result["title"], items


st.set_page_config(page_title="SNS Media Downloader")

st.title("SNS Media Downloader")
st.caption("인스타그램 게시물·릴스·스토리, X(트위터) 게시물을 원본 화질로 다운로드합니다.")

url = st.text_input(
    "게시물 URL",
    placeholder="https://www.instagram.com/... 또는 https://x.com/.../status/...",
)
cookie_file = st.file_uploader(
    "cookies.txt (선택 — 비공개 게시물·스토리 등 로그인 필요 콘텐츠)",
    type=["txt"],
)

if "media" not in st.session_state:
    st.session_state["media"] = []
    st.session_state["title"] = ""

if st.button("추출", type="primary", disabled=not url.strip()):
    cookie_bytes = cookie_file.getvalue() if cookie_file is not None else None
    with st.spinner("추출 중..."):
        try:
            title, items = extract_media(url.strip(), cookie_bytes)
        except AppError as exc:
            st.session_state["media"] = []
            st.error(ERROR_MESSAGES.get(exc.code, exc.message))
        except Exception as exc:  # noqa: BLE001
            st.session_state["media"] = []
            st.error(f"오류가 발생했습니다: {exc}")
        else:
            if not items:
                st.warning("다운로드할 미디어가 없습니다.")
            st.session_state["media"] = items
            st.session_state["title"] = title

media = st.session_state.get("media") or []
if media:
    if st.session_state.get("title"):
        st.caption(st.session_state["title"])
    for item in media:
        if item["type"] == "image":
            st.image(item["data"])
        elif item["type"] == "video":
            st.video(item["data"])
        elif item["type"] == "audio":
            st.audio(item["data"])
        st.download_button(
            label=f"다운로드 ({item['ext']})",
            data=item["data"],
            file_name=item["id"],
            mime=item["mime"],
            key=f"dl-{item['id']}",
        )
