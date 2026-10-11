import { describe, expect, it, vi } from "vitest";
import { apiFetch, ApiError } from "@/lib/api";

describe("API client", () => {
  it("turns an API error into ApiError", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: "No session" }), { status: 401 })));
    await expect(apiFetch("/private")).rejects.toMatchObject({ status: 401, message: "No session" });
    expect(await Promise.resolve(new ApiError("x", 400))).toBeInstanceOf(ApiError);
  });
});
