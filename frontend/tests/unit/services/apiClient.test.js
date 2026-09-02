import { describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => {
  const requestInterceptor = { current: null };
  const create = vi.fn(() => ({
    interceptors: {
      request: {
        use: vi.fn((fn) => {
          requestInterceptor.current = fn;
        }),
      },
    },
  }));
  return { requestInterceptor, create };
});

vi.mock("axios", () => ({
  default: {
    create: mocks.create,
  },
}));

describe("apiClient", () => {
  it("crea el cliente con la baseURL esperada y withCredentials", async () => {
    const { default: apiClient } = await import("../../../src/services/apiClient");

    expect(mocks.create).toHaveBeenCalledWith({
      baseURL: "/api",
      headers: { "Content-Type": "application/json" },
      withCredentials: true,
    });
    expect(apiClient).toBeDefined();
  });

  it("agrega header X-Timezone en las peticiones", async () => {
    await import("../../../src/services/apiClient");

    const config = mocks.requestInterceptor.current({ headers: {} });

    expect(config.headers["X-Timezone"]).toBeDefined();
  });
});