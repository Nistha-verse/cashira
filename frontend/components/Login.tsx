"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { PrototypeBanner } from "@/components/PrototypeBanner";
import { Button, Input } from "@/components/ui";
import { useSession } from "@/context/SessionContext";
import { api, ApiError } from "@/lib/api";
import { lenderStrings as s } from "@/lib/strings";

export function Login({ role }: { role: "lender" | "merchant" }) {
  const router = useRouter();
  const { signIn } = useSession();
  const [phone, setPhone] = useState<string>(role === "lender" ? s.phoneHintLender : s.phoneHintMerchant);
  const [code, setCode] = useState("");
  const [requested, setRequested] = useState(false);
  const [demoCode, setDemoCode] = useState("123456");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function requestOtp(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try { const result = await api.requestOtp(phone, role); setRequested(true); if (result.demo_code) setDemoCode(result.demo_code); setMessage(result.message || "A simulated OTP is ready."); }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : s.unreachable); }
    finally { setBusy(false); }
  }

  async function verify(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try { const result = await api.verifyOtp(phone, code, role); signIn({ token: result.session_token, role: result.role, phone: result.phone, merchantId: result.merchant_id, lenderId: result.lender_id }); router.push(role === "lender" ? "/lender" : "/merchant"); }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : s.unreachable); }
    finally { setBusy(false); }
  }

  return <><main className="auth-page"><section className="auth-card"><span className="eyebrow">{role === "lender" ? "01 / Lender" : "02 / Shopkeeper"}</span><h1>{role === "lender" ? s.lenderLogin : s.merchantLogin}</h1><form className="auth-form" onSubmit={requested ? verify : requestOtp}><div><label className="field-label" htmlFor="phone">{s.phone}</label><Input id="phone" type="tel" value={phone} onChange={(event) => setPhone(event.target.value)} required /></div>{requested && <div><label className="field-label" htmlFor="code">{s.otp}</label><Input id="code" inputMode="numeric" value={code} onChange={(event) => setCode(event.target.value)} required /></div>} {error && <div className="auth-message" role="alert">{error}</div>}{message && <div className="auth-message" aria-live="polite">{message}</div>}<Button type="submit" disabled={busy}>{requested ? s.verifyOtp : s.requestOtp}</Button></form><p className="auth-hint">{s.otpHint} <strong>{demoCode}</strong><br />{role === "lender" ? s.phoneHintLender : s.phoneHintMerchant}</p></section></main><PrototypeBanner /></>;
}
