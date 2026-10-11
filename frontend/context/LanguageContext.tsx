"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { merchantCatalog, type MerchantLanguage, type MerchantStringKey } from "@/lib/i18n";

type MerchantText = Record<MerchantStringKey, string>;
const LanguageContext = createContext<{ language: MerchantLanguage; setLanguage: (language: MerchantLanguage) => void; t: MerchantText }>({ language: "en", setLanguage: () => {}, t: merchantCatalog.en });
export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<MerchantLanguage>("en");
  useEffect(() => { const saved = localStorage.getItem("cashira.language"); if (saved === "hi" || saved === "bn") setLanguageState(saved); }, []);
  function setLanguage(value: MerchantLanguage) { localStorage.setItem("cashira.language", value); setLanguageState(value); }
  return <LanguageContext.Provider value={{ language, setLanguage, t: merchantCatalog[language] }}>{children}</LanguageContext.Provider>;
}
export const useLanguage = () => useContext(LanguageContext);
