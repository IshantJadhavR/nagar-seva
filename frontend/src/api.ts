const BASE: string = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://127.0.0.1:8000";
const KEY = "ct_session";

export interface Session { token: string; role: string; name: string }

export function loadSession(): Session | null {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Session) : null;
  } catch {
    return null;
  }
}
export function saveSession(s: Session | null) {
  try {
    if (s) localStorage.setItem(KEY, JSON.stringify(s));
    else localStorage.removeItem(KEY);
  } catch { /* storage may be blocked */ }
}

let onUnauthorized: () => void = () => {};
export function setUnauthorizedHandler(fn: () => void) { onUnauthorized = fn; }

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) { super(message); this.status = status; }
}

function errorText(body: unknown, fallback: string): string {
  const d = (body as { detail?: unknown } | null)?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((x: { msg?: string }) => x.msg ?? "invalid").join("; ");
  return fallback;
}

export async function api<T>(path: string, opts: { method?: string; json?: unknown; form?: FormData } = {}): Promise<T> {
  const headers: Record<string, string> = {};
  const s = loadSession();
  if (s) headers["Authorization"] = `Bearer ${s.token}`;
  let body: BodyInit | undefined;
  if (opts.json !== undefined) { headers["Content-Type"] = "application/json"; body = JSON.stringify(opts.json); }
  if (opts.form) body = opts.form;
  let res: Response;
  try {
    res = await fetch(BASE + path, { method: opts.method ?? (body ? "POST" : "GET"), headers, body });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Is the backend running on " + BASE + "?");
  }
  if (res.status === 401 && s) onUnauthorized();
  let data: unknown = null;
  try { data = await res.json(); } catch { /* empty body */ }
  if (!res.ok) throw new ApiError(res.status, errorText(data, res.statusText));
  return data as T;
}

export const imageUrl = (name: string) => `${BASE}/uploads/${name}`;
