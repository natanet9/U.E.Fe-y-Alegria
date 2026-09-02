import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../../src/services/apiClient", () => ({
  default: {
    get: vi.fn(),
  },
}));

import apiClient from "../../../src/services/apiClient";
import { getDashboardData } from "../../../src/services/dashboardService";

describe("dashboardService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("consulta el endpoint /dashboard/", async () => {
    apiClient.get.mockResolvedValue({ data: { ok: true } });

    const result = await getDashboardData();

    expect(apiClient.get).toHaveBeenCalledWith("/dashboard/", { params: undefined });
    expect(result).toEqual({ ok: true });
  });
});