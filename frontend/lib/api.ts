import type { Action, ActionResponse, Alert, DetailResponse, PortfolioResponse, Receipt, Transaction } from "./types";

export class ApiError extends Error {
  status: number;
  payload: unknown;
  constructor(message: string, status: number, payload?: unknown) { super(message); this.name = "ApiError"; this.status = status; this.payload = payload; }
}

const baseUrl = () => (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

export async function apiFetch<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  let response: Response;
  try { response = await fetch(`${baseUrl()}${path}`, { ...options, headers, cache: "no-store" }); }
  catch { throw new ApiError("The backend could not be reached.", 0); }
  const payload = await response.json().catch(() => undefined);
  if (!response.ok) {
    const message = typeof payload === "object" && payload && "error" in payload ? String(payload.error) : `Request failed (${response.status})`;
    throw new ApiError(message, response.status, payload);
  }
  return payload as T;
}

const query = (params: Record<string, string | number | undefined>) => { const value = new URLSearchParams(); Object.entries(params).forEach(([key, item]) => { if (item !== undefined && item !== "") value.set(key, String(item)); }); const text = value.toString(); return text ? `?${text}` : ""; };

export const api = {
  requestOtp: (phone: string, role: "lender" | "merchant") => apiFetch<{ demo_code?: string; message?: string }>(role === "lender" ? "/auth/lender/request-otp" : "/auth/request-otp", { method: "POST", body: JSON.stringify({ phone }) }),
  verifyOtp: (phone: string, code: string, role: "lender" | "merchant") => apiFetch<{ session_token: string; role: "lender" | "merchant"; phone?: string; merchant_id?: number; lender_id?: number }>(role === "lender" ? "/auth/lender/verify-otp" : "/auth/verify-otp", { method: "POST", body: JSON.stringify({ phone, code }) }),
  portfolio: (token: string) => apiFetch<PortfolioResponse>("/lender/portfolio", {}, token),
  evaluate: (token: string) => apiFetch<{ merchants_evaluated?: number; alerts?: number }>("/lender/evaluate", { method: "POST" }, token),
  merchantDetail: (id: number, token: string, lang = "en") => apiFetch<DetailResponse>(`/lender/merchants/${id}${query({ lang })}`, {}, token),
  alerts: (token: string, params: { status?: string; severity?: string; lang?: string } = {}) => apiFetch<{ alerts?: Alert[] }>(`/lender/alerts${query(params)}`, {}, token),
  alertAction: (id: number, action: "acknowledge" | "dismiss", token: string) => apiFetch<{ alert_id?: number; status?: string }>(`/lender/alerts/${id}/${action}`, { method: "POST" }, token),
  createAction: (id: number, body: { type: string; note: string; alert_id?: number; lang?: string }, token: string) => apiFetch<ActionResponse>(`/lender/merchants/${id}/actions`, { method: "POST", body: JSON.stringify(body) }, token),
  actions: (id: number, token: string) => apiFetch<{ actions?: Action[] }>(`/lender/merchants/${id}/actions`, {}, token),
  receipt: (id: number) => apiFetch<{ record?: Receipt }>(`/records/${id}/receipt`),
  verify: (body: { record_id?: number; record?: Record<string, unknown>; hash?: string; signature?: string }) => apiFetch<{ verified?: boolean; hash_valid?: boolean; signature_valid?: boolean; chain_valid?: boolean; message?: string }>("/records/verify", { method: "POST", body: JSON.stringify(body) }),
  me: (token: string) => apiFetch<{ merchant?: { id?: number; name?: string; city?: string; business_type?: string; consented_at?: string; preferred_language?: string } }>("/merchant/me", {}, token),
  consent: (token: string) => apiFetch<{ consent?: { scope?: string; status?: string; granted_at?: string; expires_at?: string | null; revoked_at?: string | null; text?: string } }>("/merchant/consent", {}, token),
  revokeConsent: (token: string) => apiFetch<{ consent?: { status?: string; scope?: string }; message?: string }>("/merchant/consent/revoke", { method: "POST" }, token),
  transactions: (token: string, from?: string, to?: string, lang = "en") => apiFetch<{ records?: Transaction[]; count?: number }>(`/merchant/transactions${query({ from, to, lang })}`, {}, token),
  summary: (token: string, lang = "en") => apiFetch<{ months?: Array<{ month?: string; inflow?: number; outflow?: number; net?: number }>; latest_month?: { month?: string; inflow?: number; outflow?: number; net?: number } | null }>(`/merchant/summary${query({ lang })}`, {}, token),
  messages: (token: string, lang: string) => apiFetch<{ messages?: Array<{ id?: number; text?: string; language?: string }> }>(`/merchant/messages${query({ lang })}`, {}, token),
  simulateWeek: (token: string, merchant_id: number, pattern: string) => apiFetch<{ merchant_id?: number; pattern?: string; status?: string; audit_record_id?: number; transactions_added?: number }>("/demo/simulate-week", { method: "POST", body: JSON.stringify({ merchant_id, pattern }) }, token),
  resetDemo: (token: string) => apiFetch<{ reset?: boolean; seed?: Record<string, unknown> }>("/demo/reset", { method: "POST" }, token)
};
