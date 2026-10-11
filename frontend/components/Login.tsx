"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button, Input } from "@/components/ui";
import { useSession } from "@/context/SessionContext";
import { useLanguage } from "@/context/LanguageContext";
import { api, ApiError } from "@/lib/api";
import { lenderStrings as s } from "@/lib/strings";

export function Login({ role }: { role: "lender" | "merchant" }) {
  const router = useRouter(); const { signIn } = useSession(); const { language, t } = useLanguage();
  const merchant = role === "merchant";
  const [phone, setPhone] = useState<string>(merchant ? s.phoneHintMerchant : s.phoneHintLender);
  const [code, setCode] = useState(""); const [requested, setRequested] = useState(false); const [demoCode, setDemoCode] = useState("123456"); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      if (!requested) { const result = await api.requestOtp(phone, role, language); setRequested(true); setDemoCode(result.demo_code || "123456"); }
      else { const result = await api.verifyOtp(phone, code, role, language); if (result.role !== role || !result.session_token) throw new Error(s.unreachable); signIn({ token: result.session_token, role: result.role, phone: result.phone, merchantId: result.merchant_id, lenderId: result.lender_id }); router.push(merchant ? "/merchant" : "/lender"); }
    } catch (caught) { setError(merchant ? caught instanceof ApiError && caught.status > 0 ? t.invalidLogin : t.error : caught instanceof ApiError && caught.status > 0 ? caught.message : s.unreachable); }
    finally { setBusy(false); }
  }
  const title = merchant ? t.login : s.lenderLogin;
  return <main className="auth-page"><section className="auth-card"><h1 aria-label={title}>{Array.from(title).map((letter, index) => <span aria-hidden="true" key={index} style={{ "--i": index } as React.CSSProperties}>{letter}</span>)}</h1><form className="auth-form" onSubmit={submit}><label><span className="field-label">{merchant ? t.phone : s.phone}</span><Input type="tel" autoComplete="tel" value={phone} onChange={event => { setPhone(event.target.value); setRequested(false); }} required /></label>{requested && <label><span className="field-label">{merchant ? t.otp : s.otp}</span><Input inputMode="numeric" autoComplete="one-time-code" value={code} onChange={event => setCode(event.target.value)} required /></label>}{error && <p className="form-error" role="alert">{error}</p>}<Button type="submit" disabled={busy}>{requested ? merchant ? t.verifyOtp : s.verifyOtp : merchant ? t.requestOtp : s.requestOtp}</Button></form><p className="auth-hint">{merchant ? t.otpHint : s.otpHint} <strong>{demoCode}</strong><br />{merchant ? t.demoPhones : s.phoneHintLender}</p></section></main>;
}
