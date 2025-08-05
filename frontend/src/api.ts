// src/api.ts
export const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "/api";

// 例：一个通用 fetch 函数
export async function postJson<T>(path: string, body: any): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as T;
}
