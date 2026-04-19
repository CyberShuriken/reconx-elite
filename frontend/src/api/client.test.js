import MockAdapter from "axios-mock-adapter";

import { api, formatApiErrorDetail, setAuthHandlers } from "./client";

describe("formatApiErrorDetail", () => {
  it("returns empty string for nullish", () => {
    expect(formatApiErrorDetail(null)).toBe("");
    expect(formatApiErrorDetail(undefined)).toBe("");
  });

  it("returns string detail as-is", () => {
    expect(formatApiErrorDetail("bad")).toBe("bad");
  });

  it("joins Pydantic-style validation list", () => {
    const detail = [{ msg: "first", type: "value_error" }, { foo: "bar" }];
    expect(formatApiErrorDetail(detail)).toBe('first; {"foo":"bar"}');
  });

  it("reads msg from object detail", () => {
    expect(formatApiErrorDetail({ msg: "oops" })).toBe("oops");
  });
});

describe("api 401 refresh interceptor", () => {
  let mock;

  beforeEach(() => {
    mock = new MockAdapter(api);
    setAuthHandlers({
      getTokens: () => ({ accessToken: "old", refreshToken: "r" }),
      refreshTokens: async () => ({ accessToken: "new", refreshToken: "r2" }),
      logout: jest.fn(),
    });
  });

  afterEach(() => {
    mock.restore();
    setAuthHandlers({
      getTokens: () => null,
      refreshTokens: async () => {
        throw new Error("reset");
      },
      logout: () => {},
    });
  });

  it("refreshes and retries once on 401", async () => {
    mock.onGet("/targets").replyOnce(401).onGet("/targets").reply(200, { ok: true });
    const out = await api.get("/targets");
    expect(out.data).toEqual({ ok: true });
  });

  it("does not retry auth refresh endpoint on 401", async () => {
    mock.onPost("/auth/refresh").reply(401);
    await expect(api.post("/auth/refresh", {})).rejects.toMatchObject({
      response: { status: 401 },
    });
  });
});
