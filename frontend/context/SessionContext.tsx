"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { clearSession, readSession, saveSession } from "@/lib/session";
import type { Role, Session } from "@/lib/types";

interface SessionContextValue { session: Session | null; ready: boolean; signIn: (session: Session) => void; signOut: () => void; }
const SessionContext = createContext<SessionContextValue | undefined>(undefined);
export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null); const [ready, setReady] = useState(false);
  useEffect(() => { setSession(readSession()); setReady(true); }, []);
  const value = useMemo(() => ({ session, ready, signIn: (next: Session) => { saveSession(next); setSession(next); }, signOut: () => { clearSession(); setSession(null); } }), [session, ready]);
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}
export function useSession() { const context = useContext(SessionContext); if (!context) throw new Error("useSession must be used within SessionProvider"); return context; }
export function useRole(role: Role) { const { session } = useSession(); return session?.role === role ? session : null; }
