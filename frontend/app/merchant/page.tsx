"use client";
import Link from "next/link";
import { useCallback, useRef, useState } from "react";
import { useLanguage } from "@/context/LanguageContext";
import { useMerchant } from "@/context/MerchantContext";
import { api } from "@/lib/api";
import { useResource } from "@/lib/useResource";
import { MerchantMessages, MerchantSalesChart, MerchantState } from "@/components/MerchantContent";
import { DateValue } from "@/components/Values";
import { Button, Card } from "@/components/ui";

export default function MerchantHome() {
  const { language, t } = useLanguage(); const { token, merchant, consent, refresh } = useMerchant(); const dialog = useRef<HTMLDialogElement>(null); const [busy, setBusy] = useState(false); const [error, setError] = useState(false);
  const load = useCallback(() => api.summary(token, language), [token, language]); const summary = useResource(`${token}:${language}`, load);
  async function revoke() { setBusy(true); setError(false); try { await api.revokeConsent(token, language); dialog.current?.close(); refresh(); } catch { setError(true); } finally { setBusy(false); } }
  return <main className="merchant-shell"><span className="eyebrow">{t.welcome}</span><h1 className="page-title">{merchant.name || t.shop}</h1><p>{t.greeting}</p><div className="merchant-stack"><Card><h2 className="section-title">{t.consent}</h2><p>{consent.text || t.consentDescription}</p><dl className="consent-details"><div><dt>{t.status}</dt><dd>● {t.active}</dd></div><div><dt>{t.since}</dt><dd><DateValue value={consent.granted_at} language={language} /></dd></div></dl><p>{t.stopSharingSimulated}</p><Button className="button-quiet" onClick={() => dialog.current?.showModal()}>{t.stopSharing}</Button></Card><section><h2 className="section-title">{t.latestMessages}</h2><MerchantMessages limit={3} /><Link className="button button-quiet" href="/merchant/messages">{t.viewMessages}</Link></section><Card><h2 className="section-title">{t.monthlySales}</h2>{summary.loading || summary.error ? <MerchantState {...summary} retry={summary.refresh} /> : summary.data?.months?.length ? <MerchantSalesChart monthly points={summary.data.months.slice(-6).map(month => ({ label: month.month || "—", value: month.inflow || 0 }))} /> : <p>{t.noTransactions}</p>}<Link className="button button-quiet" href="/merchant/sales">{t.viewSales}</Link></Card></div><dialog ref={dialog} className="confirm-dialog" aria-labelledby="consent-confirm"><h2 id="consent-confirm" className="section-title">{t.stopSharingConfirm}</h2><p>{t.stopSharingSimulated}</p>{error && <p className="form-error" role="alert">{t.error}</p>}<div className="inline-actions"><Button className="button-quiet" onClick={() => dialog.current?.close()}>{t.cancel}</Button><Button disabled={busy} onClick={() => void revoke()}>{t.confirm}</Button></div></dialog></main>;
}
