import { storage } from "@/src/utils/storage";

const BASE = `${process.env.EXPO_PUBLIC_BACKEND_URL}/api`;
export const TOKEN_KEY = "auth_token";

async function authHeaders(): Promise<Record<string, string>> {
  const token = await storage.secureGet<string>(TOKEN_KEY, "");
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function handle(res: Response) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error((data && data.detail) || "Request failed");
  }
  return data;
}

export const api = {
  async post(path: string, body?: unknown) {
    const res = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers: await authHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    });
    return handle(res);
  },
  async put(path: string, body?: unknown) {
    const res = await fetch(`${BASE}${path}`, {
      method: "PUT",
      headers: await authHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    });
    return handle(res);
  },
  async get(path: string) {
    const res = await fetch(`${BASE}${path}`, { headers: await authHeaders() });
    return handle(res);
  },
  async del(path: string) {
    const res = await fetch(`${BASE}${path}`, {
      method: "DELETE",
      headers: await authHeaders(),
    });
    return handle(res);
  },
};
