import { describe, expect, it } from "vitest";
import { merchantCatalog } from "@/lib/i18n";

describe("merchant i18n catalog", () => {
  it("has matching keys for all supported languages", () => {
    const keys = Object.keys(merchantCatalog.en).sort();
    expect(Object.keys(merchantCatalog.hi).sort()).toEqual(keys);
    expect(Object.keys(merchantCatalog.bn).sort()).toEqual(keys);
  });
});
