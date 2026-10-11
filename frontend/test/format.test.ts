import { describe, expect, it } from "vitest";
import { formatMoney } from "@/lib/format";

describe("formatMoney", () => {
  it("uses Indian rupee grouping", () => expect(formatMoney(250000)).toBe("₹2,50,000"));
  it("handles missing amounts", () => expect(formatMoney(null)).toBe("—"));
});
