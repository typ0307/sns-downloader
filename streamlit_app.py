import mimetypes
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from app.errors import AppError
from app.services.cookies import CookieFile
from app.services.extractor import Extractor
from app.services.storage import LocalStorage
from app.utils.urls import detect_platform

LOCALES = {
    "ko": "한국어",
    "en": "English",
    "ja": "日本語",
    "zh": "中文",
}

MESSAGES = {
    "ko": {
        "title": "SNS Media Downloader",
        "caption": "인스타그램 게시물·릴스·스토리, X(트위터) 게시물을 원본 화질로 다운로드합니다.",
        "url_label": "게시물 URL",
        "url_placeholder": "https://www.instagram.com/... 또는 https://x.com/.../status/...",
        "cookie_label": "cookies.txt (선택 — 비공개 게시물·스토리 등 로그인 필요 콘텐츠)",
        "extract": "추출",
        "extracting": "추출 중...",
        "no_media": "다운로드할 미디어가 없습니다.",
        "download": "다운로드",
        "unexpected_error": "오류가 발생했습니다: {error}",
        "errors": {
            "UNSUPPORTED_URL": "지원하지 않는 URL입니다. Instagram과 X(Twitter) 링크만 지원합니다.",
            "EXTRACT_FAILED": "미디어 추출에 실패했습니다. 링크를 확인하거나 cookies.txt를 업로드해 보세요.",
            "LOGIN_REQUIRED": "로그인이 필요합니다. 유효한 cookies.txt를 업로드하세요.",
            "RATE_LIMITED": "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.",
            "MEDIA_NOT_FOUND": "미디어를 찾을 수 없습니다.",
            "INVALID_COOKIE_FILE": "cookies.txt 파일 형식이 올바르지 않습니다.",
        },
    },
    "en": {
        "title": "SNS Media Downloader",
        "caption": "Download Instagram posts, reels, stories, and X (Twitter) posts in original quality.",
        "url_label": "Post URL",
        "url_placeholder": "https://www.instagram.com/... or https://x.com/.../status/...",
        "cookie_label": "cookies.txt (optional — for private posts, stories, and other login-required content)",
        "extract": "Extract",
        "extracting": "Extracting...",
        "no_media": "No media available to download.",
        "download": "Download",
        "unexpected_error": "An error occurred: {error}",
        "errors": {
            "UNSUPPORTED_URL": "Unsupported URL. Only Instagram and X (Twitter) links are supported.",
            "EXTRACT_FAILED": "Failed to extract media. Check the link or upload a cookies.txt.",
            "LOGIN_REQUIRED": "Login required. Please upload a valid cookies.txt.",
            "RATE_LIMITED": "Too many requests. Please try again later.",
            "MEDIA_NOT_FOUND": "Media not found.",
            "INVALID_COOKIE_FILE": "Invalid cookies.txt file format.",
        },
    },
    "ja": {
        "title": "SNS Media Downloader",
        "caption": "Instagram の投稿・リール・ストーリー、X(Twitter) の投稿をオリジナル画質でダウンロードします。",
        "url_label": "投稿URL",
        "url_placeholder": "https://www.instagram.com/... または https://x.com/.../status/...",
        "cookie_label": "cookies.txt（任意 — 非公開投稿・ストーリーなどログインが必要なコンテンツ）",
        "extract": "抽出",
        "extracting": "抽出中...",
        "no_media": "ダウンロードできるメディアがありません。",
        "download": "ダウンロード",
        "unexpected_error": "エラーが発生しました: {error}",
        "errors": {
            "UNSUPPORTED_URL": "対応していないURLです。Instagram と X(Twitter) のリンクのみ対応しています。",
            "EXTRACT_FAILED": "メディアの抽出に失敗しました。リンクを確認するか cookies.txt をアップロードしてください。",
            "LOGIN_REQUIRED": "ログインが必要です。有効な cookies.txt をアップロードしてください。",
            "RATE_LIMITED": "リクエストが多すぎます。しばらくしてから再度お試しください。",
            "MEDIA_NOT_FOUND": "メディアが見つかりません。",
            "INVALID_COOKIE_FILE": "cookies.txt の形式が正しくありません。",
        },
    },
    "zh": {
        "title": "SNS Media Downloader",
        "caption": "以原始画质下载 Instagram 帖子、Reels、Stories 和 X(Twitter) 帖子。",
        "url_label": "帖子链接",
        "url_placeholder": "https://www.instagram.com/... 或 https://x.com/.../status/...",
        "cookie_label": "cookies.txt（可选 — 用于私密帖子、Stories 等需要登录的内容）",
        "extract": "提取",
        "extracting": "提取中...",
        "no_media": "没有可下载的媒体。",
        "download": "下载",
        "unexpected_error": "发生错误：{error}",
        "errors": {
            "UNSUPPORTED_URL": "不支持的链接。仅支持 Instagram 和 X(Twitter) 链接。",
            "EXTRACT_FAILED": "媒体提取失败。请检查链接或上传 cookies.txt。",
            "LOGIN_REQUIRED": "需要登录。请上传有效的 cookies.txt。",
            "RATE_LIMITED": "请求过于频繁，请稍后再试。",
            "MEDIA_NOT_FOUND": "未找到媒体。",
            "INVALID_COOKIE_FILE": "cookies.txt 文件格式不正确。",
        },
    },
}


def extract_media(url: str, cookie_bytes: bytes | None):
    platform = detect_platform(url)
    if platform is None:
        raise AppError("UNSUPPORTED_URL", "Unsupported URL.", 400)

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

st.sidebar.selectbox(
    "Language",
    options=list(LOCALES),
    format_func=LOCALES.get,
    key="lang",
)

lang = st.session_state.get("lang", "ko")
t = MESSAGES[lang]

st.title(t["title"])
st.caption(t["caption"])

url = st.text_input(
    t["url_label"],
    placeholder=t["url_placeholder"],
)
cookie_file = st.file_uploader(
    t["cookie_label"],
    type=["txt"],
)

if "media" not in st.session_state:
    st.session_state["media"] = []
    st.session_state["title"] = ""

if st.button(t["extract"], type="primary", disabled=not url.strip()):
    cookie_bytes = cookie_file.getvalue() if cookie_file is not None else None
    with st.spinner(t["extracting"]):
        try:
            title, items = extract_media(url.strip(), cookie_bytes)
        except AppError as exc:
            st.session_state["media"] = []
            st.error(t["errors"].get(exc.code, exc.message))
        except Exception as exc:  # noqa: BLE001
            st.session_state["media"] = []
            st.error(t["unexpected_error"].format(error=exc))
        else:
            if not items:
                st.warning(t["no_media"])
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
            label=f"{t['download']} ({item['ext']})",
            data=item["data"],
            file_name=item["id"],
            mime=item["mime"],
            key=f"dl-{item['id']}",
        )
