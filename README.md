# sns-downloader

인스타그램, X(트위터), 그리고 Pinterest의 미디어를 고화질(원본 화질)로 빠르고
쉽게 다운로드하는 Streamlit 웹 앱입니다.

- 인스타그램: 게시물·릴스·스토리(캐러셀·하이라이트 포함)
- X(트위터): 게시물(이미지·동영상)
- Pinterest: 개별 핀(동영상·스토리 핀·이미지)
- 다국어 UI: 한국어 / English / 日本語 / 中文

비공개·연령 제한 콘텐츠와 인스타그램 스토리는 로그인이 필요하며, `cookies.txt`
업로드로 인증할 수 있습니다.

## 주요 기능

- 인스타그램 게시물·릴스·스토리·하이라이트, X 게시물, Pinterest 개별 핀 다운로드
- 캐러셀(여러 장) 자동 분리 다운로드
- 스토리는 사진(이미지)·동영상 모두 지원 (스토리는 게시 후 약 24시간 유효)
- `cookies.txt` 업로드로 로그인 필요 콘텐츠 접근
- 다국어 UI (한국어/English/日本語/中文) — 사이드바에서 전환

## 기술 스택

- UI/앱: Streamlit (기본 컴포넌트)
- 추출: yt-dlp (버전 고정: `yt-dlp==2026.7.4`)
- 배포: Streamlit Community Cloud

## 프로젝트 구조

```
streamlit_app.py   Streamlit 앱 (UI + 다국어 i18n)
app/               추출 로직 패키지 (yt-dlp 기반)
  errors.py        오류 코드 (AppError)
  services/
    extractor.py   미디어 추출 (게시물·릴·스토리·X)
    cookies.py     cookies.txt 검증/임시 파일
    storage.py     로컬 임시 저장 (메모리 기반)
  utils/
    urls.py        플랫폼 감지 / URL 검증
requirements.txt   파이썬 의존성 (streamlit + yt-dlp)
packages.txt       시스템 패키지 (ffmpeg)
```

## 로컬 실행

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

브라우저에서 `http://localhost:8501`을 열고 URL을 붙여넣어 다운로드합니다.

## Streamlit Community Cloud 배포

1. GitHub에 push → [share.streamlit.io](https://share.streamlit.io)에서 **New app**
2. 저장소와 브랜치 선택, **Main file path**를 `streamlit_app.py`로 지정
3. Deploy — 루트 `requirements.txt`(streamlit, yt-dlp)와 `packages.txt`(ffmpeg)가 자동 설치됩니다
4. 완료되면 `https://<앱이름>.streamlit.app`에서 사용

미디어는 요청마다 임시 디렉터리에 담아 `st.download_button`으로 즉시 전달하며,
영구 저장소를 사용하지 않습니다.

### 앱 슬립(수면) 방지

Community Cloud는 **트래픽이 12시간 없으면 앱이 슬립**합니다. 자동으로
깨우려면 무료 모니터링 서비스로 앱의 상태 확인 엔드포인트를 주기적으로
호출하세요:

- [UptimeRobot](https://uptimerobot.com) (무료) → Monitor URL:
  `https://<앱이름>.streamlit.app/_stcore/health`, 간격 5분
- 또는 [cron-job.org](https://cron-job.org) (무료)에서 같은 URL을 5~10분 간격 호출

주기적 호출이 "트래픽"으로 인식되어 슬립되지 않습니다. 이미 슬립된 경우에는
앱에 접속해 "Yes, get this app back up!" 버튼으로 깨울 수 있습니다.

> 무료 티어 리소스 한도(메모리 약 2.7GB)가 있어 초대용량 동영상은 제한될 수
> 있습니다.

## cookies.txt 사용법

로그인이 필요한 콘텐츠(비공개 게시물, 스토리 등)는 브라우저에서 내보낸
Netscape 형식의 `cookies.txt`를 업로드하세요.

1. 브라우저 확장 프로그램(예: "Get cookies.txt LOCALLY")으로
   `instagram.com`(또는 `x.com`)의 쿠키를 `cookies.txt`로 내보냅니다.
2. 앱의 "cookies.txt" 업로드 영역에 파일을 첨부합니다.
3. URL을 입력하고 추출합니다.

> Community Cloud에서는 브라우저 세션 기능을 사용할 수 없으므로
> `cookies.txt` 업로드 방식을 사용합니다.
