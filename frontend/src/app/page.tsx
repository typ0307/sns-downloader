"use client";

import { useEffect, useState } from "react";
import { ApiError, extractMedia, mediaUrl, previewUrl } from "@/lib/api";
import type { ExtractResponse } from "@/lib/api";
import {
  LOCALES,
  errorMessage,
  formatItemCount,
  getMessages,
  mediaTypeLabel,
  useLocale,
  type Locale,
} from "@/lib/i18n";

function formatBytes(bytes: number): string {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

const BROWSERS = [
  { id: "chrome", label: "Chrome" },
  { id: "edge", label: "Edge" },
  { id: "firefox", label: "Firefox" },
  { id: "safari", label: "Safari" },
  { id: "brave", label: "Brave" },
  { id: "opera", label: "Opera" },
];

function detectBrowser(): string {
  if (typeof navigator === "undefined") return "chrome";
  const ua = navigator.userAgent;
  if (ua.includes("Edg/")) return "edge";
  if (ua.includes("OPR/") || ua.includes("Opera")) return "opera";
  if (ua.includes("Firefox/")) return "firefox";
  if (ua.includes("Safari/") && !ua.includes("Chrome/")) return "safari";
  return "chrome";
}

export default function Home() {
  const [locale, setLocale] = useLocale();
  const [url, setUrl] = useState("");
  const [useBrowserSession, setUseBrowserSession] = useState(false);
  const [browser, setBrowser] = useState(detectBrowser);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ExtractResponse | null>(null);
  const t = getMessages(locale);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await extractMedia(url, useBrowserSession ? browser : undefined);
      setResult(res);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? errorMessage(err.code, err.message, locale)
          : t.unexpectedError
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-6 py-12">
      <div className="flex justify-end">
        <select
          value={locale}
          onChange={(e) => setLocale(e.target.value as Locale)}
          aria-label="Language"
          className="rounded-lg border border-zinc-300 bg-white px-2 py-1 text-xs text-zinc-600 outline-none focus:border-zinc-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
        >
          {LOCALES.map((l) => (
            <option key={l.code} value={l.code}>
              {l.label}
            </option>
          ))}
        </select>
      </div>

      <header className="flex flex-col gap-2 text-center">
        <h1 className="text-3xl font-semibold tracking-tight">SNS Media Downloader</h1>
        <p className="text-zinc-500">{t.subtitle}</p>
      </header>

      <form
        onSubmit={onSubmit}
        className="flex flex-col gap-4 rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900"
      >
        <div className="flex flex-col gap-1.5">
          <label htmlFor="url" className="text-sm font-medium">
            {t.postUrl}
          </label>
          <input
            id="url"
            type="url"
            required
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder={t.urlPlaceholder}
            className="rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500 dark:border-zinc-700 dark:bg-zinc-950"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <label className="flex cursor-pointer items-center gap-2 text-sm text-zinc-600 dark:text-zinc-300">
            <input
              type="checkbox"
              checked={useBrowserSession}
              onChange={(e) => setUseBrowserSession(e.target.checked)}
              className="h-4 w-4 rounded border-zinc-300 accent-zinc-900 dark:accent-zinc-100"
            />
            {t.useBrowserSession}
          </label>
          {useBrowserSession && (
            <select
              value={browser}
              onChange={(e) => setBrowser(e.target.value)}
              aria-label="Browser"
              className="rounded-lg border border-zinc-300 bg-white px-2 py-1 text-xs text-zinc-600 outline-none focus:border-zinc-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
            >
              {BROWSERS.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.label}
                </option>
              ))}
            </select>
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-zinc-900 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white"
        >
          {loading ? t.extracting : t.extract}
        </button>
      </form>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      {result && (
        <section className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium uppercase dark:bg-zinc-800">
                {result.platform}
              </span>
              <span className="text-xs text-zinc-500">
                {formatItemCount(result.media.length, locale)}
              </span>
            </div>
            {result.title && (
              <p className="line-clamp-3 text-sm text-zinc-600 dark:text-zinc-400">
                {result.title}
              </p>
            )}
          </div>

          <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {result.media.map((item) => (
              <li
                key={item.id}
                className="flex flex-col gap-3 overflow-hidden rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900"
              >
                {item.type === "image" ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={previewUrl(item)}
                    alt=""
                    className="h-48 w-full bg-zinc-100 object-cover dark:bg-zinc-800"
                  />
                ) : item.type === "audio" ? (
                  <div className="flex h-48 w-full items-center justify-center bg-zinc-100 px-4 dark:bg-zinc-800">
                    <audio src={previewUrl(item)} controls className="w-full" />
                  </div>
                ) : (
                  <video
                    src={previewUrl(item)}
                    controls
                    className="h-48 w-full bg-zinc-100 object-contain dark:bg-zinc-800"
                  />
                )}
                <div className="flex items-center justify-between gap-2 px-4 pb-4">
                  <div className="flex items-center gap-2 text-xs text-zinc-500">
                    <span className="rounded bg-zinc-100 px-1.5 py-0.5 font-mono uppercase dark:bg-zinc-800">
                      {mediaTypeLabel(item.type, locale)}
                    </span>
                    <span className="font-mono">{item.ext}</span>
                    <span>{formatBytes(item.size_bytes)}</span>
                  </div>
                  <a
                    href={item.direct_url ?? mediaUrl(item.download_url)}
                    {...(item.direct_url
                      ? { target: "_blank", rel: "noopener noreferrer" }
                      : { download: true })}
                    className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white"
                  >
                    {t.download}
                  </a>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
