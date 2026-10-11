"use client";
import { useLanguage } from "@/context/LanguageContext";
import type { MerchantLanguage } from "@/lib/i18n";
export function LanguageSwitcher() {
  const { language, setLanguage, t } = useLanguage();
  return <label className="language-switcher"><span className="sr-only">{t.language}</span><select className="line-input" value={language} onChange={event => setLanguage(event.target.value as MerchantLanguage)}><option value="en">{t.english}</option><option value="hi">{t.hindi}</option><option value="bn">{t.bengali}</option></select></label>;
}
