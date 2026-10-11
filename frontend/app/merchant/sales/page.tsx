"use client";
import { useCallback, useState } from "react";
import { useLanguage } from "@/context/LanguageContext";
import { useMerchant } from "@/context/MerchantContext";
import { api } from "@/lib/api";
import { useResource } from "@/lib/useResource";
import { MerchantSalesChart, MerchantState } from "@/components/MerchantContent";
import { Money, DateValue } from "@/components/Values";
import { Button, Card, Input } from "@/components/ui";
export default function SalesPage() {
  const { t, language } = useLanguage(); const { token } = useMerchant(); const [from, setFrom] = useState(""); const [to, setTo] = useState(""); const [range, setRange] = useState({ from: "", to: "" }); const [invalid, setInvalid] = useState(false);
  const load = useCallback(() => api.transactions(token, range.from, range.to, language), [token, range, language]); const resource = useResource(`${token}:${language}:${range.from}:${range.to}`, load);
  const all = resource.data?.records || [];
  const lastDay = all[all.length - 1]?.date; const cutoff = lastDay ? new Date(new Date(lastDay).getTime() - 29 * 86400000).toISOString().slice(0, 10) : "";
  const records = range.from || range.to ? all : all.filter(item => (item.date || "") >= cutoff);
  const totals = new Map<string, number>(); records.forEach(item => { if (item.direction === "inflow" && item.date) totals.set(item.date, (totals.get(item.date) || 0) + (item.amount || 0)); });
  return <main className="merchant-shell"><h1 className="page-title">{t.sales}</h1><form className="merchant-filter" onSubmit={event => { event.preventDefault(); if (from && to && from > to) { setInvalid(true); return; } setInvalid(false); setRange({ from, to }); }}><label><span className="field-label">{t.from}</span><Input type="date" value={from} onChange={event => setFrom(event.target.value)} /></label><label><span className="field-label">{t.to}</span><Input type="date" value={to} onChange={event => setTo(event.target.value)} /></label><Button type="submit">{t.filter}</Button></form>{invalid && <p role="alert" className="form-error">{t.invalidRange}</p>}{resource.loading || resource.error ? <MerchantState {...resource} retry={resource.refresh} /> : records.length ? <><Card><MerchantSalesChart points={Array.from(totals, ([label, value]) => ({ label, value }))} /></Card><h2 className="section-title">{t.recentTransactions}</h2><div className="merchant-stack">{[...records].reverse().map(item => <Card className="transaction-row" key={item.id}><DateValue value={item.date} language={language} /><span>{item.direction === "inflow" ? t.inflow : t.outflow}</span><Money value={item.amount} /></Card>)}</div></> : <p className="state">{t.noTransactions}</p>}</main>;
}
