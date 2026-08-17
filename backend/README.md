# sns-downloader backend

인스타그램과 X(트위터) 미디어를 추출·저장·스트리밍하는 FastAPI 백엔드입니다.
미디어 추출은 yt-dlp(버전 고정)를 사용합니다.

## 요구사항

- Python 3.14 이상
- [uv](https://docs.astral.sh/uv/)

## 설치 및 실행

```sh
cd backend
uv sync              # 가상환경 생성 및 의존성 설치
uv run uvicorn app.main:app --reload --port 8000
```

동작 확인:

```sh
curl http://127.0.0.1:8000/api/health
# {"status":"ok"}
```

## 환경 설정

선택적 설정은 `backend/.env` 파일에서 읽습니다 (`backend/.env.example` 참고).

| 환경 변수 | 기본값 | 설명 |
|---|---|---|
| `CORS_ORIGINS` | `*` | 프론트엔드가 API를 직접 호출할 때 허용할 출처(쉼표 구분) |
| `STORAGE_DIR` | `data` | 다운로드한 미디어를 저장할 디렉터리 |
| `MAX_UPLOAD_BYTES` | `1048576` | 업로드할 수 있는 cookies.txt 최대 크기(바이트) |
| `RATE_LIMIT` | `10/minute` | `/api/extract` 요청 제한 (slowapi 문법) |
| `COOKIES_FROM_BROWSER` | (없음) | 모든 요청에 적용할 브라우저 쿠키 소스 (예: `chrome`) |

`COOKIES_FROM_BROWSER` 지원 값: `chrome`, `chromium`, `edge`, `firefox`,
`safari`, `brave`, `opera`, `vivaldi`, `whale` 및 모바일 변형.

## API

### POST /api/extract

`multipart/form-data` 요청으로 URL을 받아 미디어 목록을 반환합니다.

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `url` | text | 예 | 다운로드할 게시물/스토리/릴스 URL |
| `cookie_file` | file | 아니요 | Netscape 형식 `cookies.txt` |
| `browser` | text | 아니요 | 브라우저 쿠키 소스 이름 (예: `chrome`) |

성공 응답:

```json
{
  "id": "job-...",
  "platform": "instagram",
  "title": "Story by aespa_official",
  "media": [
    {
      "id": "abcdef12-00-3f9a.jpg",
      "type": "image",
      "ext": "jpg",
      "size_bytes": 194496,
      "download_url": "/api/download/abcdef12-00-3f9a.jpg",
      "direct_url": "https://scontent-..."
    }
  ]
}
```

### GET /api/download/{media_id}

저장된 미디어를 스트리밍합니다. `?inline=1` 쿼리로 브라우저에 직접
표시(미리보기)할 수 있습니다.

### GET /api/health

```json
{"status": "ok"}
```

## 오류 응답

오류는 `{ "error": { "code", "message" } }` 형식으로 반환됩니다.

| code | HTTP 상태 | 설명 |
|---|---|---|
| `UNSUPPORTED_URL` | 400 | 지원하지 않는 URL |
| `LOGIN_REQUIRED` | 401 | 로그인 필요 (cookies.txt 또는 브라우저 세션 필요) |
| `RATE_LIMITED` | 429 | 요청 제한 초과 |
| `MEDIA_NOT_FOUND` | 404 | 미디어를 찾을 수 없음 |
| `EXTRACT_FAILED` | 502 | 미디어 추출 실패 |
| `INVALID_COOKIE_FILE` | 400 | cookies.txt 형식 오류 |

## 인증 (로그인 필요 콘텐츠)

비공개 게시물, 연령 제한 콘텐츠, 인스타그램 스토리는 인증이 필요합니다.
두 가지 방법 중 하나를 사용합니다.

### cookies.txt 업로드

브라우저 확장 프로그램 등으로 로그인 세션을 Netscape 형식 `cookies.txt`로
내보내어 `cookie_file`로 업로드합니다. 업로드된 파일은 해당 요청에서만
사용되는 임시 파일(`0600` 권한)로 저장되며, 요청이 끝나면 즉시 삭제됩니다.

### 브라우저 세션

백엔드가 실행되는 머신의 로그인된 브라우저에서 쿠키를 직접 읽습니다.
`browser` 필드에 브라우저 이름을 보내거나, 환경 변수
`COOKIES_FROM_BROWSER`로 모든 요청에 적용할 수 있습니다.

- 백엔드와 브라우저가 같은 머신에 있어야 합니다.
- macOS에서 Chrome/Edge는 키체인 접근이 잠겨 있으면 쿠키를 복호화할 수
  없으므로 키체인을 잠금 해제해야 합니다.

## 인스타그램 스토리 추출

- 스토리는 게시 후 약 24시간이 지나면 만료됩니다. 만료된 스토리는
  `EXTRACT_FAILED`로 "This Instagram story has expired or is no longer
  available." 메시지가 반환됩니다.
- 사진 스토리는 이미지로, 동영상 스토리는 최고 해상도의 동영상으로
  다운로드됩니다.
- `/stories/<user>/<id>`: 해당 스토리 하나만 다운로드
- `/stories/<user>/`: 해당 계정의 현재 스토리를 모두 다운로드
- `/stories/highlights/<id>`: 해당 하이라이트의 모든 항목 다운로드

## 프로젝트 구조

```
app/
  main.py              FastAPI 앱 생성, CORS, 예외 처리
  api/routes.py        /api/health, /api/extract, /api/download
  services/
    extractor.py       yt-dlp 기반 추출 + 스토리 전용 추출
    cookies.py         cookies.txt 검증/임시 저장
    storage.py         미디어 파일 저장/조회
  utils/urls.py        URL 플랫폼 감지
  config.py            환경 설정 (pydantic-settings)
  errors.py            오류 코드 정의
  limiter.py           요청 제한 (slowapi)
  models.py            Pydantic 응답 모델
```
