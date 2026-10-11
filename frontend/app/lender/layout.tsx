"use client";
import { Nav } from "@/components/Nav";
import { PrototypeBanner } from "@/components/PrototypeBanner";
import { RoleGuard } from "@/components/RoleGuard";
export default function LenderLayout({ children }: { children: React.ReactNode }) { return <RoleGuard><Nav /><div>{children}</div><PrototypeBanner /></RoleGuard>; }
