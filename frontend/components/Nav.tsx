"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useSession } from "@/context/SessionContext";
import { lenderStrings as s } from "@/lib/strings";
import { Button } from "./ui";
import { LanguageSwitcher } from "./LanguageSwitcher";

export function Nav({ merchant = false }: { merchant?: boolean }) { const path = usePathname(); const router = useRouter(); const { session, signOut } = useSession(); const base = merchant ? "/merchant" : "/lender"; return <header className="top-nav"><Link className="logo" href={session ? base : "/"}>{s.logo}</Link><nav className="nav-pill" aria-label="Main navigation">{merchant ? <><Link className={path === "/merchant" ? "active" : ""} href="/merchant">{s.open}</Link><Link className={path.includes("messages") ? "active" : ""} href="/merchant/messages">{s.alerts}</Link><Link className={path.includes("sales") ? "active" : ""} href="/merchant/sales">{s.portfolio}</Link></> : <><Link className={path === "/lender" ? "active" : ""} href="/lender">{s.portfolio}</Link><Link className={path.includes("alerts") ? "active" : ""} href="/lender/alerts">{s.alerts}</Link><Link className={path.startsWith("/records") ? "active" : ""} href="/records">{s.records}</Link><Link className={path.includes("demo") ? "active" : ""} href="/lender/demo">{s.demo}</Link></>}</nav><div className="nav-actions">{merchant ? <LanguageSwitcher /> : <span className="role-badge">{session?.role || s.lender}</span>}{session && <Button className="button-quiet" onClick={() => { signOut(); router.push(merchant ? "/merchant/login" : "/lender/login"); }}>{s.signOut}</Button>}</div></header>; }
