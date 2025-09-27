// TEMP: Hardcode backend API base for validation
export const API_BASE: string = "http://backend-alb-948465488.us-west-2.elb.amazonaws.com";

// Debug: print which backend URL the frontend resolved
try {
  const rawBack = undefined as any;
  const rawAlt = undefined as any;
  if (typeof window !== "undefined") {
    // eslint-disable-next-line no-console
    console.info("[Frontend] Hardcoded API_BASE override in use");
    // eslint-disable-next-line no-console
    console.info("[Frontend] VITE_API_BASE_URL:", rawAlt);
    // eslint-disable-next-line no-console
    console.info("[Frontend] API_BASE (resolved):", API_BASE);
    // Expose for quick checks in dev tools
    (window as any).__API_BASE__ = API_BASE;
  }
} catch {}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    headers: { "Accept": "application/json" },
  });
  return handleResponse<T>(res);
}

export async function apiPost<T>(path: string, body?: any): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Accept": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return handleResponse<T>(res);
}

export async function apiPatch<T>(path: string, body?: any): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", "Accept": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return handleResponse<T>(res);
}

export async function apiDelete<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: { "Accept": "application/json" },
  });
  // Many DELETE endpoints return no body
  if (res.status === 204) return undefined as unknown as T;
  return handleResponse<T>(res);
}
