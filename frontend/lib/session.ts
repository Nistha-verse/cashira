import type { Role, Session } from "./types";

export const SESSION_KEY = "cashira.session";
export function readSession(): Session | null { if (typeof window === "undefined") return null; try { const value = sessionStorage.getItem(SESSION_KEY); return value ? JSON.parse(value) as Session : null; } catch { return null; } }
export function saveSession(session: Session) { sessionStorage.setItem(SESSION_KEY, JSON.stringify(session)); }
export function clearSession() { sessionStorage.removeItem(SESSION_KEY); }
export function resolveRoleRedirect(pathname: string, session: Session | null): string | null {
  if (pathname.startsWith("/lender") && pathname !== "/lender/login" && session?.role !== "lender") return session?.role === "merchant" ? "/merchant" : "/lender/login";
  if (pathname.startsWith("/merchant") && pathname !== "/merchant/login" && session?.role !== "merchant") return session?.role === "lender" ? "/lender" : "/merchant/login";
  return null;
}

export function loginForRole(role: Role): string { return role === "lender" ? "/lender/login" : "/merchant/login"; }
