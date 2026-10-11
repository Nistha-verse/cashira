import { formatDate, formatMoney } from "@/lib/format";
export function Money({ value }: { value?: number | null }) { return <span className="money">{formatMoney(value)}</span>; }
export function DateValue({ value, language = "en" }: { value?: string | null; language?: string }) { return <time dateTime={value || undefined}>{formatDate(value, language)}</time>; }
