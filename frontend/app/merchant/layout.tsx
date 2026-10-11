"use client";
import { Nav } from "@/components/Nav";
import { PrototypeBanner } from "@/components/PrototypeBanner";
import { RoleGuard } from "@/components/RoleGuard";
export default function MerchantLayout({ children }: { children: React.ReactNode }) { return <RoleGuard><Nav merchant /><div>{children}</div><PrototypeBanner /></RoleGuard>; }
