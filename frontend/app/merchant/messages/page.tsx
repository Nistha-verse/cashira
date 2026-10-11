"use client";
import { useLanguage } from "@/context/LanguageContext";
import { MerchantMessages } from "@/components/MerchantContent";
export default function MessagesPage() { const { t } = useLanguage(); return <main className="merchant-shell"><h1 className="page-title">{t.messages}</h1><p>{t.newest}</p><MerchantMessages /></main>; }
