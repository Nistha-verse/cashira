import type { Metadata } from "next";
import { Anton, Inter, Noto_Sans_Bengali, Noto_Sans_Devanagari } from "next/font/google";
import { SessionProvider } from "@/context/SessionContext";
import { NoiseOverlay } from "@/components/NoiseOverlay";
import "./globals.css";

const anton = Anton({ subsets: ["latin"], weight: "400", variable: "--font-anton" });
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const devanagari = Noto_Sans_Devanagari({ subsets: ["devanagari"], variable: "--font-devanagari" });
const bengali = Noto_Sans_Bengali({ subsets: ["bengali"], variable: "--font-bengali" });
export const metadata: Metadata = { title: "Cashira — cash-flow intelligence", description: "A synthetic cash-flow intelligence prototype for lender review." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en" className={`${anton.variable} ${inter.variable} ${devanagari.variable} ${bengali.variable}`}><body><SessionProvider><NoiseOverlay />{children}</SessionProvider></body></html>; }
