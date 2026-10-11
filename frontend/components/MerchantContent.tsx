"use client";
import { useCallback } from "react";
import { Line, LineChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useLanguage } from "@/context/LanguageContext";
import { useMerchant } from "@/context/MerchantContext";
import { api } from "@/lib/api";
import { useResource } from "@/lib/useResource";
import { formatMoney } from "@/lib/format";
import { Money } from "./Values";
import { Card } from "./ui";

export function MerchantState({ loading, error, retry }: { loading?: boolean; error?: unknown; retry: () => void }) { const { t } = useLanguage(); return <div className={`state ${error ? "error-state" : ""}`} role={error ? "alert" : "status"}>{loading ? t.loading : t.error}{!!error && <button className="button" onClick={retry}>{t.retry}</button>}</div>; }
export function MerchantMessages({ limit }: { limit?: number }) {
  const { token } = useMerchant(); const { language, t } = useLanguage();
  const load = useCallback(() => api.messages(token, language), [token, language]); const resource = useResource(`${token}:${language}`, load);
  if (resource.loading || resource.error) return <MerchantState {...resource} retry={resource.refresh} />;
  const messages = resource.data?.messages || [];
  return messages.length ? <div className="merchant-stack">{messages.slice(0, limit).map((message, index) => <Card key={message.id || index}><p>{message.text || t.unavailable}</p><p className="message-caption">{t.dateMissing}</p><p className="message-caption">{t.simulatedMessage}</p></Card>)}</div> : <p className="state">{t.noMessages}</p>;
}
export function MerchantSalesChart({ points, monthly = false }: { points: Array<{ label: string; value: number }>; monthly?: boolean }) {
  const { t } = useLanguage();
  return <figure className="merchant-chart"><ResponsiveContainer width="100%" height={280}><LineChart data={points} margin={{ left: 3, right: 16, top: 20, bottom: 35 }}><CartesianGrid stroke="var(--moss)" strokeDasharray="3 3" /><XAxis dataKey="label" tick={{ fill: "var(--forest)", fontSize: 11 }} label={{ value: monthly ? t.month : t.date, position: "bottom", fill: "var(--forest)" }} /><YAxis width={75} tickFormatter={value => formatMoney(value).replace(/\.00$/, "")} tick={{ fill: "var(--forest)", fontSize: 10 }} /><Tooltip formatter={value => formatMoney(Number(value))} /><Legend verticalAlign="top" /><Line dataKey="value" name={t.sales} stroke="var(--forest)" strokeWidth={3} dot={false} isAnimationActive={false} /></LineChart></ResponsiveContainer><figcaption>{t.rupees}. {t.total}: <Money value={points.reduce((sum, item) => sum + item.value, 0)} /></figcaption></figure>;
}
