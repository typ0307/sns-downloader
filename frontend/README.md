# sns-downloader frontend

sns-downloader의 Next.js 16(App Router, TypeScript) 프론트엔드입니다.
URL을 붙여넣어 미디어를 추출하고 다운로드하는 UI를 제공합니다.

## 요구사항

- Node.js 20 이상
- npm

## 설치 및 실행

```sh
cd frontend
npm install
npm run dev       # 개발 서버 (http://localhost:3000)
```

프로덕션 빌드:

```sh
npm run build
npm start
```

## 환경 변수

### BACKEND_URL (개발 프록시 대상)

`next.config.ts`가 `/api/*` 요청을 백엔드로 프록시합니다. 백엔드가 다른
주소에서 실행 중이면 설정합니다.

```sh
BACKEND_URL=http://127.0.0.1:8000 npm run dev
```

기본값은 `http://127.0.0.1:8000`입니다.

### NEXT_PUBLIC_API_URL (브라우저에서 직접 호출)

`src/lib/api.ts`는 `NEXT_PUBLIC_API_URL`이 설정되어 있으면 브라우저가
백엔드를 직접 호출합니다(프록시 미사용). 백엔드가 프론트엔드와 다른 호스트에
있거나 CORS가 허용된 경우 설정합니다.

```sh
NEXT_PUBLIC_API_URL=http://192.168.0.10:8000 npm run dev
```

설정하지 않으면 빈 문자열로 처리되어 같은 출처(프록시)로 요청합니다.

## 사용법

1. 다운로드할 링크를 입력합니다.
   - 인스타그램: `/p/`, `/reel/`, `/stories/<user>/<id>`, `/stories/highlights/<id>`
   - X(트위터): `/user/status/<id>`
2. 로그인이 필요한 콘텐츠(비공개 게시물, 스토리)라면 "로그인된 브라우저 세션
   사용" 체크박스를 켜고 브라우저를 선택합니다. (백엔드와 같은 머신의
   브라우저여야 합니다. 또는 별도의 `cookies.txt` 업로드를 통해 인증)
3. "추출"을 누르면 미디어 미리보기와 다운로드 버튼이 표시됩니다.
   - 이미지/동영상/오디오 미리보기 지원
   - 여러 장(캐러셀, 스토리 목록)은 각각 개별 항목으로 표시
   - 직접 URL이 있는 미디어는 원본 링크로 열 수 있습니다.

## 다국어 (i18n)

한국어/English/日本語/中文을 지원하며, 우측 상단의 선택 메뉴로 전환할 수
있습니다. 선택한 언어는 `localStorage`에 저장되고, 브라우저 언어 설정이
기본값으로 사용됩니다.

새 문구를 추가하려면 `src/lib/i18n.ts`의 `messages` 객체에 4개 언어 모두
추가하면 됩니다.

## 프로젝트 구조

```
src/
  app/
    layout.tsx         루트 레이아웃 (메타데이터, 다국어 lang)
    page.tsx           메인 페이지 (URL 입력, 결과/미리보기 UI)
    globals.css        전역 스타일 (Tailwind CSS)
    favicon.ico
  lib/
    api.ts             백엔드 API 호출 (extract/download/preview URL)
    i18n.ts            다국어 문구와 로케일 관리
```

## 스크립트

| 스크립트 | 설명 |
|---|---|
| `npm run dev` | 개발 서버 실행 |
| `npm run build` | 프로덕션 빌드 |
| `npm start` | 프로덕션 서버 실행 |
| `npm run lint` | ESLint 검사 |
