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
frontend/          Next.js 앱 (UI)
backend/           FastAPI 앱 (API + 미디어 추출)
```

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
