// Server-side fetch helper. Forwards request cookies to the K2-Board backend.
//
// In production (single Railway container) the FastAPI backend listens on
// 127.0.0.1:8000 inside the same container, so server components hit it
// directly via INTERNAL_API_URL — no extra hop through the Next.js rewrite.
// In local dev the backend is a separate uvicorn process, same address.

import { cookies } from "next/headers";

const API_BASE =
  process.env.INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

type FetchOptions = RequestInit & { signal?: AbortSignal };

export async function apiFetch<T>(path: string, init?: FetchOptions): Promise<T> {
  const jar = await cookies();
  const cookieHeader = jar.getAll().map(c => `${c.name}=${c.value}`).join("; ");
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      cookie: cookieHeader,
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body || res.statusText);
  }
  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(public status: number, body: string) {
    super(`API ${status}: ${body}`);
  }
}

export const API_BASE_URL = API_BASE;
