"use client";
import { Login } from "@/components/Login";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { PrototypeBanner } from "@/components/PrototypeBanner";
export default function MerchantLoginPage() { return <><div className="login-language"><LanguageSwitcher /></div><Login role="merchant" /><PrototypeBanner /></>; }
