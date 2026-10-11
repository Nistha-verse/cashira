"use client";

import { useEffect, useState } from "react";
import { merchantCatalog, type MerchantLanguage } from "@/lib/i18n";
import { Select } from "./ui";

export function LanguageSwitcher() { const [language, setLanguage] = useState<MerchantLanguage>("en"); useEffect(() => { const value = localStorage.getItem("cashira.language"); if (value === "en" || value === "hi" || value === "bn") setLanguage(value); }, []); function change(value: MerchantLanguage) { setLanguage(value); localStorage.setItem("cashira.language", value); window.dispatchEvent(new CustomEvent("cashira-language-change")); } return <label className="language-switcher"><span className="sr-only">{merchantCatalog[language].language}</span><Select aria-label={merchantCatalog[language].language} value={language} onChange={(event) => change(event.target.value as MerchantLanguage)}><option value="en">EN</option><option value="hi">हिन्दी</option><option value="bn">বাংলা</option></Select></label>; }
