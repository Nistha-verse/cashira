"use client";
import { usePathname } from "next/navigation";
import { Nav } from "@/components/Nav";
import { PrototypeBanner } from "@/components/PrototypeBanner";
import { RoleGuard } from "@/components/RoleGuard";
import { MerchantProvider } from "@/context/MerchantContext";
import { LanguageProvider, useLanguage } from "@/context/LanguageContext";
function MerchantShell({ children }: { children: React.ReactNode }) {
  const { language, t } = useLanguage(); const path = usePathname();
  return <div lang={language} className={`merchant-ui language-${language}`}><Nav merchant /><RoleGuard>{path === "/merchant/login" ? children : <MerchantProvider>{children}</MerchantProvider>}</RoleGuard><footer className="merchant-footer">{t.footer}</footer><PrototypeBanner /></div>;
}
export default function MerchantLayout({ children }: { children: React.ReactNode }) { return <LanguageProvider><MerchantShell>{children}</MerchantShell></LanguageProvider>; }
