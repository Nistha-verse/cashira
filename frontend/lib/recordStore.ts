const key = "cashira.record-ids";

export function readRecordIds(): number[] {
  if (typeof window === "undefined") return [];
  try { const value = JSON.parse(sessionStorage.getItem(key) || "[]"); return Array.isArray(value) ? value.filter((item): item is number => typeof item === "number") : []; } catch { return []; }
}

export function rememberRecordId(id: number | null | undefined) {
  if (!id || typeof window === "undefined") return;
  const ids = Array.from(new Set([id, ...readRecordIds()])); sessionStorage.setItem(key, JSON.stringify(ids));
}
