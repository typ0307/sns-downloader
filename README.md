# sns-downloader

인스타그램과 X(트위터)의 미디어를 고화질(원본 화질)로 빠르고 쉽게 다운로드하는
웹 도구입니다.

- 인스타그램: 게시물·릴스·스토리(캐러셀·하이라이트 포함)
- X(트위터): 게시물(이미지·동영상)

비공개·연령 제한 콘텐츠와 인스타그램 스토리는 로그인이 필요하며, `cookies.txt`
업로드 또는 로그인된 브라우저 세션으로 인증할 수 있습니다.

## 주요 기능

- 인스타그램 게시물·릴스·스토리·하이라이트, X 게시물 다운로드
- 캐러셀(여러 장) 자동 분리 다운로드
- 스토리는 사진(이미지)·동영상 모두 지원 (스토리는 게시 후 약 24시간 유효)
- `cookies.txt` 업로드 또는 브라우저 세션으로 로그인 필요 콘텐츠 접근
- 다국어 UI (한국어/English/日本語/中文)

## 기술 스택

- 프론트엔드: Next.js 16 (App Router, TypeScript) — 자세한 내용은 [frontend/README.md](frontend/README.md)
- 백엔드: FastAPI (Python 3.14) + uvicorn, uv로 관리 — 자세한 내용은 [backend/README.md](backend/README.md)
- 추출: yt-dlp (버전 고정)

## 프로젝트 구조

```
streamlit_app.py   Streamlit 앱 (Community Cloud 배포용 단일 앱)
requirements.txt   Streamlit 앱 의존성 (streamlit + yt-dlp)
packages.txt       Streamlit 앱 시스템 패키지 (ffmpeg)
frontend/          Next.js 앱 (UI)
backend/           FastAPI 앱 (API + 미디어 추출, Streamlit에서 재사용)
```

## Streamlit 앱 배포 (Community Cloud)

단일 Streamlit 앱으로 간단하게 배포하려면:

1. GitHub에 push → [share.streamlit.io](https://share.streamlit.io)에서 **New app**
2. 저장소와 브랜치 선택, **Main file path**를 `streamlit_app.py`로 지정
3. Deploy — 루트 `requirements.txt`(streamlit, yt-dlp)와 `packages.txt`(ffmpeg)가 자동 설치됩니다
4. 완료되면 `https://<앱이름>.streamlit.app`에서 사용

Streamlit 앱은 `backend/app/`의 추출 로직(yt-dlp)을 그대로 재사용하며, 미디어를
메모리에 담아 `st.download_button`으로 즉시 전달하므로 영구 저장소가 없습니다.

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
> 있습니다. 별도 서버(FastAPI) 배포는 아래 "배포" 절을 참고하세요.

## 배포

- **프론트엔드**: Vercel에 배포합니다. 빌드 환경 변수로
  `NEXT_PUBLIC_API_URL`을 백엔드 공개 URL로 설정하세요.
  (예: `https://<username>.pythonanywhere.com`)
- **백엔드**: PythonAnywhere에 배포합니다 (`backend/wsgi.py` + `requirements.txt`).
  상세 절차는 [backend/README.md](backend/README.md)의 "배포" 섹션을 참고하세요.
- 배포 환경에서는 브라우저 세션 기능 대신 **cookies.txt 업로드** 방식을
  사용합니다.

## 빠른 시작

백엔드와 프론트엔드를 각각 실행합니다.

### 1. 백엔드

```sh
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

동작 확인: `curl http://127.0.0.1:8000/api/health` → `{"status":"ok"}`

자세한 내용: [backend/README.md](backend/README.md)

### 2. 프론트엔드

```sh
cd frontend
npm install
npm run dev
```

http://localhost:3000 을 열고 URL을 붙여넣어 다운로드합니다. 개발 서버는
`/api/*` 요청을 백엔드 `http://127.0.0.1:8000`으로 자동 프록시합니다.

자세한 내용: [frontend/README.md](frontend/README.md)

## API 개요

| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/extract` | URL을 받아 미디어 목록 반환 |
| GET | `/api/download/{media_id}` | 미디어 파일 스트리밍 |
| GET | `/api/health` | 헬스 체크 |

전체 API 명세와 오류 코드는 [backend/README.md](backend/README.md)를 참고하세요.
