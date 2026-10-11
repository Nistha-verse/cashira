"use client";
import { createContext, useCallback, useContext } from "react";
import { api } from "@/lib/api";
import { useResource } from "@/lib/useResource";
import { useSession } from "./SessionContext";
import { useLanguage } from "./LanguageContext";
import { Card } from "@/components/ui";

type Consent = NonNullable<Awaited<ReturnType<typeof api.consent>>["consent"]>;
type Merchant = NonNullable<Awaited<ReturnType<typeof api.me>>["merchant"]>;
const MerchantContext = createContext<{ consent: Consent; merchant: Merchant; token: string; refresh: () => void } | null>(null);
export function MerchantProvider({ children }: { children: React.ReactNode }) {
  const { session } = useSession(); const { language, t } = useLanguage(); const token = session?.token || "";
  const load = useCallback(async () => { const [consent, me] = await Promise.all([api.consent(token, language), api.me(token, language)]); return { consent: consent.consent, merchant: me.merchant }; }, [token, language]);
  const resource = useResource(`${token}:${language}`, load);
  const consent = resource.data?.consent;
  if (resource.loading) return <main className="merchant-shell"><p className="state" role="status">{t.loading}</p></main>;
  if (resource.error || !consent) return <main className="merchant-shell"><div className="state error-state" role="alert"><p>{t.error}</p><button className="button" onClick={resource.refresh}>{t.retry}</button></div></main>;
  const withdrawn = consent.status !== "active" || !!consent.revoked_at || (!!consent.expires_at && new Date(consent.expires_at).getTime() < Date.now());
  if (withdrawn) return <main className="merchant-shell"><Card className="withdrawn-state"><span className="withdrawn-icon" aria-hidden="true">⊘</span><h1 className="section-title">{t.withdrawn}</h1><p>{t.noData}</p></Card></main>;
  return <MerchantContext.Provider value={{ consent, merchant: resource.data?.merchant || {}, token, refresh: resource.refresh }}>{children}</MerchantContext.Provider>;
}
export function useMerchant() { const context = useContext(MerchantContext); if (!context) throw new Error("Merchant context unavailable"); return context; }
