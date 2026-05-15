// Client-side API helper. Cookies are auto-sent with credentials: "include".

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export interface ApiClientError extends Error {
  status: number;
  body: string;
}

export async function apiClient<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const body = await res.text();
    const err = new Error(`API ${res.status}: ${body || res.statusText}`) as ApiClientError;
    err.status = res.status;
    err.body = body;
    throw err;
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}
