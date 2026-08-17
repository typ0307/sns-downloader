# sns-downloader

인스타그램과 X(트위터)의 미디어를 고화질(원본 화질)로 빠르고 쉽게 다운로드하는
웹 도구입니다.

인스타그램의 게시물·릴스·스토리(캐러셀·하이라이트 포함)와 X(트위터) 게시물
링크를 붙여넣고, 비공개·연령 제한 콘텐츠(및 스토리)를 받으려면 `cookies.txt`를
업로드하거나 로그인된 브라우저 세션을 사용하면 됩니다.

## 기술 스택

- 프론트엔드: Next.js 16 (App Router, TypeScript)
- 백엔드: FastAPI (Python 3.14) + uvicorn, uv로 관리
- 추출: yt-dlp (버전 고정)

## 프로젝트 구조

```
frontend/          Next.js 앱
backend/           FastAPI 앱 (app/, pyproject.toml)
```

## 시작하기

### 백엔드 (uv)

```sh
cd backend
uv sync              # Python 3.14 가상환경 생성 및 의존성 설치
uv run uvicorn app.main:app --reload --port 8000
```

동작 확인:

```sh
curl http://127.0.0.1:8000/api/health
# {"status":"ok"}
```

선택적 설정은 `backend/.env`에서 읽습니다 (`backend/.env.example` 참고).

### 프론트엔드 (npm)

```sh
cd frontend
npm install
npm run dev
```

http://localhost:3000 을 엽니다. 개발 서버는 `/api/*` 요청을 백엔드
`http://127.0.0.1:8000`으로 자동 프록시합니다 (`next.config.ts` 참고).

백엔드가 다른 호스트에서 실행 중이라면 `frontend/.env.local`에
`NEXT_PUBLIC_API_URL`을 설정하면 프록시를 거치지 않고 브라우저가 백엔드를
직접 호출합니다 (`.env.local.example` 참고).

## API

| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/extract` | `multipart/form-data`: `url`(필수) + `cookie_file` 또는 `browser`(선택). 미디어 목록 반환. |
| GET | `/api/download/{media_id}` | 미디어 파일 스트리밍 (`?inline=1`이면 미리보기). |
| GET | `/api/health` | 헬스 체크. |

오류 응답은 `{ "error": { "code", "message" } }` 형식이며 코드는
`UNSUPPORTED_URL`, `EXTRACT_FAILED`, `LOGIN_REQUIRED`, `RATE_LIMITED`,
`MEDIA_NOT_FOUND`, `INVALID_COOKIE_FILE` 입니다.

## cookies.txt

비공개 또는 연령 제한 게시물은 브라우저 확장 프로그램 등으로 로그인 세션을
Netscape 형식의 `cookies.txt`로 내보내 업로드하면 됩니다. 인스타그램 스토리
(예: `/stories/<user>/<id>` 또는 `/stories/highlights/<id>`)는 항상 로그인이
필요하므로 유효한 `cookies.txt`가 필수입니다.

업로드된 파일은 해당 요청에서만 사용되는 임시 파일(`0600` 권한)에 저장되며,
요청이 끝나면 즉시 삭제됩니다. 로그에 남거나 저장되지 않습니다.

## 브라우저 세션 사용

`cookies.txt` 대신 백엔드가 실행되는 머신의 로그인된 브라우저에서 쿠키를
직접 읽도록 할 수 있습니다. UI에서 "로그인된 브라우저 세션 사용" 체크박스를
켜고 브라우저를 선택하면 됩니다. 모든 요청에 적용하려면 백엔드 환경 변수에
`COOKIES_FROM_BROWSER=chrome`을 설정합니다 (`backend/.env.example` 참고).

- 브라우저가 백엔드와 같은 머신에 있고, 해당 사이트에 로그인되어 있어야 합니다.
- macOS에서 Chrome/Edge는 키체인 접근이 잠겨 있으면 쿠키를 복호화할 수
  없으므로 키체인을 잠금 해제해야 합니다.

## 스토리 다운로드 참고사항

- 스토리는 게시 후 약 24시간이 지나면 만료됩니다. 다운로드하려면 스토리가
  게시된 직후 링크를 붙여넣으세요. 만료된 스토리는
  "No media found. This Instagram story has expired or is no longer available."
  메시지가 표시됩니다.
- 사진 스토리는 이미지로, 동영상 스토리는 최고 해상도의 동영상으로
  다운로드됩니다. 특정 스토리 링크(`/stories/<user>/<id>`)는 해당 스토리
  하나만, `/stories/<user>/` 형태는 해당 계정의 현재 스토리를 모두 가져옵니다.
