import type { Status, Severity } from "@/lib/types";
import { lenderStrings as s } from "@/lib/strings";

const labels: Record<Status | Severity, string> = { green: s.onTrack, amber: s.watch, red: s.needsAttention, "consent withdrawn": s.consentWithdrawn, none: "No signal" };
const icons: Record<Status | Severity, string> = { green: "●", amber: "▲", red: "■", "consent withdrawn": "⊘", none: "○" };
export function statusLabel(status: Status | Severity | undefined): string { return labels[status || "none"] || "No status"; }
export function StatusChip({ status }: { status: Status | Severity | undefined }) { const safe = status || "none"; return <span className={`status-chip status-${safe.replace(" ", "-")}`}><span aria-hidden="true">{icons[safe]}</span><span>{statusLabel(safe)}</span></span>; }
