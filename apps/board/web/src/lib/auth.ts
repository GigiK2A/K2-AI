import { redirect } from "next/navigation";
import { apiFetch, ApiError } from "./api";

export interface CurrentUser {
  username: string;
}

interface MeResponse {
  user: CurrentUser;
}

export async function getCurrentUser(): Promise<CurrentUser | null> {
  try {
    const data = await apiFetch<MeResponse>("/api/auth/me");
    return data.user;
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) return null;
    throw err;
  }
}

export async function requireUser(): Promise<CurrentUser> {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  return user;
}
