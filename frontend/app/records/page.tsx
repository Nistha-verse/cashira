"use client";

import Link from "next/link";
import { useState } from "react";
import { Button, Card, Input } from "@/components/ui";
import { readRecordIds } from "@/lib/recordStore";
import { lenderStrings as s } from "@/lib/strings";

export default function RecordsPage() { const [id, setId] = useState(""); const links = typeof window === "undefined" ? [] : readRecordIds(); return <main className="page-shell"><span className="eyebrow">Verification / Receipts</span><h1 className="page-title">{s.recordsTitle}</h1><Card className="record-search"><h2 className="section-title">{s.openRecord}</h2><form onSubmit={(event) => { event.preventDefault(); if (id) window.location.href = `/records/${id}`; }}><label><span className="field-label">{s.enterRecordId}</span><Input inputMode="numeric" value={id} onChange={(event) => setId(event.target.value)} placeholder="e.g. 5" /></label><Button type="submit">{s.openRecord}</Button></form></Card><section className="record-links"><h2 className="section-title">Records collected this session</h2>{links.length ? links.map((recordId) => <Link key={recordId} className="record-link-card card" href={`/records/${recordId}`}><span className="eyebrow">{s.recordId}</span><strong>{recordId}</strong><span>{s.receipt} →</span></Link>) : <p className="state">{s.noRecordLinks}</p>}</section></main>; }
