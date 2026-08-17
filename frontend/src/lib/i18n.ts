import { useSyncExternalStore } from "react";

export type Locale = "ko" | "en" | "ja" | "zh";

export interface Messages {
  subtitle: string;
  postUrl: string;
  urlPlaceholder: string;
  useBrowserSession: string;
  extract: string;
  extracting: string;
  download: string;
  unexpectedError: string;
  typeVideo: string;
  typeImage: string;
  typeAudio: string;
  errors: Record<string, string>;
}

export const DEFAULT_LOCALE: Locale = "ko";

export const LOCALES: { code: Locale; label: string }[] = [
  { code: "ko", label: "한국어" },
  { code: "en", label: "English" },
  { code: "ja", label: "日本語" },
  { code: "zh", label: "中文" },
];

const messages: Record<Locale, Messages> = {
  ko: {
    subtitle: "인스타그램과 X(트위터)의 게시물·릴·스토리·영상을 원본 화질로 다운로드하세요.",
    postUrl: "게시물 URL",
    urlPlaceholder:
      "https://www.instagram.com/reel/... 또는 https://www.instagram.com/stories/... 또는 https://x.com/.../status/...",
    useBrowserSession: "로그인된 브라우저 세션 사용 (스토리 등 로그인 필요 콘텐츠)",
    extract: "추출",
    extracting: "추출 중…",
    download: "다운로드",
    unexpectedError: "예기치 않은 오류가 발생했습니다.",
    typeVideo: "영상",
    typeImage: "이미지",
    typeAudio: "오디오",
    errors: {
      UNSUPPORTED_URL: "지원하지 않는 URL입니다. Instagram과 X(Twitter) 링크만 지원합니다.",
      EXTRACT_FAILED: "미디어 추출에 실패했습니다.",
      LOGIN_REQUIRED: "로그인이 필요합니다. 유효한 cookies.txt를 업로드하세요.",
      RATE_LIMITED: "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.",
      MEDIA_NOT_FOUND: "미디어를 찾을 수 없습니다.",
      INVALID_COOKIE_FILE: "cookies.txt 파일 형식이 올바르지 않습니다.",
    },
  },
  en: {
    subtitle: "Download Instagram and X (Twitter) posts, reels, stories, and videos in original quality.",
    postUrl: "Post URL",
    urlPlaceholder:
      "https://www.instagram.com/reel/... or https://www.instagram.com/stories/... or https://x.com/.../status/...",
    useBrowserSession: "Use logged-in browser session (for stories and other login-required content)",
    extract: "Extract",
    extracting: "Extracting…",
    download: "Download",
    unexpectedError: "An unexpected error occurred.",
    typeVideo: "Video",
    typeImage: "Image",
    typeAudio: "Audio",
    errors: {
      UNSUPPORTED_URL: "Unsupported URL. Only Instagram and X (Twitter) links are supported.",
      EXTRACT_FAILED: "Failed to extract media.",
      LOGIN_REQUIRED: "Login required. Please upload a valid cookies.txt.",
      RATE_LIMITED: "Too many requests. Please try again later.",
      MEDIA_NOT_FOUND: "Media not found.",
      INVALID_COOKIE_FILE: "Invalid cookies.txt file format.",
    },
  },
  ja: {
    subtitle: "Instagram と X(Twitter) の投稿・リール・ストーリー・動画をオリジナル画質でダウンロードできます。",
    postUrl: "投稿URL",
    urlPlaceholder:
      "https://www.instagram.com/reel/... または https://www.instagram.com/stories/... または https://x.com/.../status/...",
    useBrowserSession: "ログイン済みブラウザのセッションを使用（ストーリーなどのログインが必要なコンテンツ）",
    extract: "抽出",
    extracting: "抽出中…",
    download: "ダウンロード",
    unexpectedError: "予期しないエラーが発生しました。",
    typeVideo: "動画",
    typeImage: "画像",
    typeAudio: "音声",
    errors: {
      UNSUPPORTED_URL: "対応していないURLです。Instagram と X(Twitter) のリンクのみ対応しています。",
      EXTRACT_FAILED: "メディアの抽出に失敗しました。",
      LOGIN_REQUIRED: "ログインが必要です。有効な cookies.txt をアップロードしてください。",
      RATE_LIMITED: "リクエストが多すぎます。しばらくしてから再度お試しください。",
      MEDIA_NOT_FOUND: "メディアが見つかりません。",
      INVALID_COOKIE_FILE: "cookies.txt の形式が正しくありません。",
    },
  },
  zh: {
    subtitle: "以原始画质下载 Instagram 和 X(Twitter) 的帖子、Reels、Stories 和视频。",
    postUrl: "帖子链接",
    urlPlaceholder:
      "https://www.instagram.com/reel/... 或 https://www.instagram.com/stories/... 或 https://x.com/.../status/...",
    useBrowserSession: "使用已登录的浏览器会话（用于 Stories 等需要登录的内容）",
    extract: "提取",
    extracting: "提取中…",
    download: "下载",
    unexpectedError: "发生意外错误。",
    typeVideo: "视频",
    typeImage: "图片",
    typeAudio: "音频",
    errors: {
      UNSUPPORTED_URL: "不支持的链接。仅支持 Instagram 和 X(Twitter) 链接。",
      EXTRACT_FAILED: "媒体提取失败。",
      LOGIN_REQUIRED: "需要登录。请上传有效的 cookies.txt。",
      RATE_LIMITED: "请求过于频繁，请稍后再试。",
      MEDIA_NOT_FOUND: "未找到媒体。",
      INVALID_COOKIE_FILE: "cookies.txt 文件格式不正确。",
    },
  },
};

export function getMessages(locale: Locale): Messages {
  return messages[locale] ?? messages[DEFAULT_LOCALE];
}

const LOCALE_KEY = "locale";
const listeners = new Set<() => void>();

function subscribe(callback: () => void): () => void {
  listeners.add(callback);
  window.addEventListener("storage", callback);
  return () => {
    listeners.delete(callback);
    window.removeEventListener("storage", callback);
  };
}

function browserLocale(): Locale {
  const lang = (window.navigator.language || "").toLowerCase();
  if (lang.startsWith("ko")) return "ko";
  if (lang.startsWith("en")) return "en";
  if (lang.startsWith("ja")) return "ja";
  if (lang.startsWith("zh")) return "zh";
  return DEFAULT_LOCALE;
}

function getSnapshot(): Locale {
  const saved = window.localStorage.getItem(LOCALE_KEY) as Locale | null;
  if (saved && LOCALES.some((l) => l.code === saved)) return saved;
  return browserLocale();
}

function getServerSnapshot(): Locale {
  return DEFAULT_LOCALE;
}

export function useLocale(): [Locale, (locale: Locale) => void] {
  const locale = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const setLocale = (next: Locale) => {
    window.localStorage.setItem(LOCALE_KEY, next);
    listeners.forEach((listener) => listener());
  };
  return [locale, setLocale];
}

export function formatItemCount(n: number, locale: Locale): string {
  switch (locale) {
    case "ko":
      return `${n}개`;
    case "ja":
      return `${n}件`;
    case "zh":
      return `${n}项`;
    default:
      return `${n} item${n === 1 ? "" : "s"}`;
  }
}

export function errorMessage(code: string, fallback: string, locale: Locale): string {
  return getMessages(locale).errors[code] ?? fallback;
}

export function mediaTypeLabel(type: string, locale: Locale): string {
  const t = getMessages(locale);
  if (type === "video") return t.typeVideo;
  if (type === "image") return t.typeImage;
  if (type === "audio") return t.typeAudio;
  return type;
}
