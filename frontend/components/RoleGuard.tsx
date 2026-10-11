"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useSession } from "@/context/SessionContext";
import { resolveRoleRedirect } from "@/lib/session";
export function RoleGuard({ children }: { children: React.ReactNode }) { const pathname = usePathname(); const router = useRouter(); const { session, ready } = useSession(); const redirect = resolveRoleRedirect(pathname, session); useEffect(() => { if (ready && redirect) router.replace(redirect); }, [ready, redirect, router]); if (!ready || redirect) return <main className="guard-loading" aria-live="polite">Loading Cashira…</main>; return <>{children}</>; }
