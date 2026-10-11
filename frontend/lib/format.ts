export function formatMoney(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(value);
}

export function formatDate(value: string | null | undefined, language = "en"): string {
  if (!value) return "—";
  const date = new Date(value.includes("T") ? value : `${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? "—" : new Intl.DateTimeFormat(`${language}-IN`, { dateStyle: "medium" }).format(date);
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)}%`;
}
