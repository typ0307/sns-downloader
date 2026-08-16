# sns-downloader

Fast and easy high-quality media downloader for Instagram and X.

Paste an Instagram post/reel (including carousels) or an X (Twitter) post link,
optionally upload a `cookies.txt` for private/age-restricted content, and
download the media in original quality.

## Stack

- Frontend: Next.js 16 (App Router, TypeScript)
- Backend: FastAPI (Python 3.14) + uvicorn, managed with uv
- Extraction: yt-dlp (pinned)

## Project layout

```
frontend/          Next.js app
backend/           FastAPI app (app/, tests/, pyproject.toml)
```

## Getting started

### Backend (uv)

```sh
cd backend
uv sync              # creates .venv with Python 3.14 and installs deps
uv run uvicorn app.main:app --reload --port 8000
```

Verify:

```sh
curl http://127.0.0.1:8000/api/health
# {"status":"ok"}
```

Run tests:

```sh
uv run pytest -q
```

Optional configuration is read from `backend/.env` (see `backend/.env.example`).

### Frontend (npm)

```sh
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. The dev server proxies `/api/*` to the backend at
`http://127.0.0.1:8000` automatically (see `next.config.ts`).

If the backend runs on a different host, set `NEXT_PUBLIC_API_URL` in
`frontend/.env.local` (see `.env.local.example`) so the browser calls it
directly instead of going through the proxy.

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/extract` | `multipart/form-data`: `url` (text) + `cookie_file` (optional). Returns media list. |
| GET | `/api/download/{media_id}` | Streams a media file (`?inline=1` for preview). |
| GET | `/api/health` | Health check. |

Error responses use `{ "error": { "code", "message" } }` with codes
`UNSUPPORTED_URL`, `EXTRACT_FAILED`, `LOGIN_REQUIRED`, `RATE_LIMITED`,
`MEDIA_NOT_FOUND`, `INVALID_COOKIE_FILE`.

## cookies.txt

For private or age-restricted posts, export your logged-in session as a
Netscape-format `cookies.txt` (e.g. via a browser extension) and upload it.
The file is stored in a temporary `0600` file, used only for that request, and
deleted immediately afterwards. It is never logged or persisted.
