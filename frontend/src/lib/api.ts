export interface MediaItem {
  id: string;
  type: "video" | "image" | "audio";
  ext: string;
  size_bytes: number;
  download_url: string;
  direct_url: string | null;
}

export interface ExtractResponse {
  id: string;
  platform: "instagram" | "x";
  title: string;
  media: MediaItem[];
}

interface ApiErrorBody {
  error: { code: string; message: string };
}

export class ApiError extends Error {
  code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.code = code;
  }
}

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/+$/, "");

export async function extractMedia(url: string): Promise<ExtractResponse> {
  const form = new FormData();
  form.append("url", url);

  const res = await fetch(`${API_URL}/api/extract`, {
    method: "POST",
    body: form,
  });

  const data = (await res.json().catch(() => ({}))) as ExtractResponse & ApiErrorBody;

  if (!res.ok) {
    throw new ApiError(
      data.error?.code ?? "EXTRACT_FAILED",
      data.error?.message ?? `Request failed with status ${res.status}.`
    );
  }

  return data;
}

export function mediaUrl(path: string): string {
  return `${API_URL}${path}`;
}

export function previewUrl(item: MediaItem): string {
  return `${mediaUrl(item.download_url)}?inline=1`;
}
