import { describe, expect, it, vi, afterEach } from "vitest";
import { api, ApiError, clock, setCsrf } from "./api";
describe("assessment time display", () => {
  it("rounds up and never shows negative time", () => {
    expect(clock(61.1)).toBe("01:02");
    expect(clock(-3)).toBe("00:00");
    expect(clock(3600)).toBe("60:00");
  });
});
describe("authenticated API transport", () => {
  afterEach(() => vi.unstubAllGlobals());
  it("includes cookies and CSRF on writes", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => ({ saved: true }) });
    vi.stubGlobal("fetch", fetcher);
    setCsrf("session-csrf");
    await api("/test", "PUT", { answer: 2 });
    expect(fetcher).toHaveBeenCalledWith(
      "/api/test",
      expect.objectContaining({
        credentials: "include",
        headers: expect.objectContaining({ "X-CSRF-Token": "session-csrf" }),
        body: '{"answer":2}',
      }),
    );
  });
  it("surfaces server errors instead of pretending to save", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 409,
        json: async () => ({ error: { message: "Assessment closed" } }),
      }),
    );
    await expect(api("/test")).rejects.toEqual(
      new ApiError(409, "Assessment closed"),
    );
  });
});
