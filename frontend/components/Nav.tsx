"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useSession } from "@/context/SessionContext";
import { useLanguage } from "@/context/LanguageContext";
import { lenderStrings as s } from "@/lib/strings";
import { Button } from "./ui";
import { LanguageSwitcher } from "./LanguageSwitcher";

export function Nav({ merchant = false }: { merchant?: boolean }) {
  const path = usePathname(); const router = useRouter(); const { session, signOut } = useSession(); const { t } = useLanguage();
  const login = path.endsWith("/login");
  const links = merchant ? [["/merchant", t.home], ["/merchant/messages", t.messages], ["/merchant/sales", t.sales]] : [["/lender", s.portfolio], ["/lender/alerts", s.alerts], ["/records", s.records]];
  return <header className="top-nav"><Link className="logo" href="/">{s.logo}</Link>{!login && <nav className="nav-pill" aria-label={t.mainNav}>{links.map(([href, title]) => <Link key={href} href={href} aria-current={path === href ? "page" : undefined} className={path === href ? "active" : ""}>{title}</Link>)}</nav>}<div className="nav-actions">{merchant ? <LanguageSwitcher /> : <span className="role-badge">{s.lender}</span>}{session && <Button className="button-quiet" onClick={() => { signOut(); router.push(merchant ? "/merchant/login" : "/lender/login"); }}>{merchant ? t.signOut : s.signOut}</Button>}</div></header>;
}
