import Link from "next/link";
import { lenderStrings as s } from "@/lib/strings";
export function Footer() { return <footer className="site-footer"><div><span className="footer-mark">{s.logo}</span><p>{s.footerNotice}</p></div><nav aria-label="Footer"><Link href="/">Home</Link><Link href="/lender/login">Lender access</Link><Link href="/merchant/login">Shopkeeper access</Link></nav><p className="footer-prototype">{s.prototype}</p></footer>; }
