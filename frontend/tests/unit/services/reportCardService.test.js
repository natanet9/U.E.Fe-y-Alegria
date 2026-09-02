import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../../src/services/apiClient", () => ({
  default: { get: vi.fn() },
}));

import apiClient from "../../../src/services/apiClient";
import { getReportCard, downloadReportCard, getConsolidado } from "../../../src/services/reportCardService";

describe("reportCardService", () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it("getReportCard consulta /report-card/ con estudiante_id y gestion", async () => {
    apiClient.get.mockResolvedValue({ data: { materias: [] } });
    const result = await getReportCard({ estudianteId: 10, gestion: "2026" });
    expect(apiClient.get).toHaveBeenCalledWith("/report-card/", {
      params: { estudiante_id: 10, gestion: "2026" },
    });
    expect(result.materias).toEqual([]);
  });

  it("downloadReportCard consulta /report-card/download/ con responseType blob", async () => {
    apiClient.get.mockResolvedValue({ data: new Blob(), headers: {} });
    const result = await downloadReportCard({ estudianteId: 10, gestion: "2026" });
    expect(apiClient.get).toHaveBeenCalledWith("/report-card/download/", {
        params: { estudiante_id: 10, gestion: "2026", fmt: "pdf" },
        responseType: "blob",
    });
    expect(result.data).toBeInstanceOf(Blob);
  });

  it("getConsolidado consulta /report-card/consolidado/", async () => {
    apiClient.get.mockResolvedValue({ data: { gestion: 2026, cursos: [] } });
    const result = await getConsolidado("2026");
    expect(apiClient.get).toHaveBeenCalledWith("/report-card/consolidado/", {
      params: { gestion: "2026" },
    });
    expect(result.gestion).toBe(2026);
  });

  it("getConsolidado sin gestion no envia params", async () => {
    apiClient.get.mockResolvedValue({ data: {} });
    await getConsolidado();
    expect(apiClient.get).toHaveBeenCalledWith("/report-card/consolidado/", {
      params: {},
    });
  });
});
