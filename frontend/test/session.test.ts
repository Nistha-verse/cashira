import { describe, expect, it } from "vitest";
import { resolveRoleRedirect } from "@/lib/session";

describe("role guards", () => {
  it("sends a merchant away from lender routes", () => expect(resolveRoleRedirect("/lender", { token: "x", role: "merchant" })).toBe("/merchant"));
  it("sends a lender away from merchant routes", () => expect(resolveRoleRedirect("/merchant/sales", { token: "x", role: "lender" })).toBe("/lender"));
  it("sends anonymous users to the matching login", () => expect(resolveRoleRedirect("/lender/alerts", null)).toBe("/lender/login"));
});
