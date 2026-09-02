import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../../src/services/apiClient", () => ({
  default: { get: vi.fn(), patch: vi.fn(), post: vi.fn() },
}));

import apiClient from "../../../src/services/apiClient";
import { getLicenciasPage, getLicenciaDetail, approveLicencia } from "../../../src/services/licenciasService";

describe("licenciasService", () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it("getLicenciasPage consulta /licencias/", async () => {
    apiClient.get.mockResolvedValue({ data: { licencias: { items: [] } } });
    const result = await getLicenciasPage({ estado: "pendiente" });
    expect(apiClient.get).toHaveBeenCalledWith("/licencias/", {
      params: { estado: "pendiente", page: 1, page_size: 10 },
    });
    expect(result.licencias.items).toEqual([]);
  });

  it("getLicenciaDetail consulta /licencias/<id>/", async () => {
    apiClient.get.mockResolvedValue({ data: { id: 5, motivo: "Enfermedad" } });
    const result = await getLicenciaDetail(5);
    expect(apiClient.get).toHaveBeenCalledWith("/licencias/5/");
    expect(result.motivo).toBe("Enfermedad");
  });

  it("approveLicencia hace PATCH a /licencias/ con aceptar=true", async () => {
    apiClient.patch.mockResolvedValue({ data: { ok: true } });
    const result = await approveLicencia(5, { aceptar: true, observaciones: "ok" });
    expect(apiClient.patch).toHaveBeenCalledWith("/licencias/", {
      licencia_id: 5,
      aceptar: true,
      observaciones: "ok",
    });
    expect(result.ok).toBe(true);
  });

  it("approveLicencia rechaza con aceptar=false", async () => {
    apiClient.patch.mockResolvedValue({ data: { ok: true } });
    await approveLicencia(5, { aceptar: false });
    expect(apiClient.patch).toHaveBeenCalledWith("/licencias/", {
      licencia_id: 5,
      aceptar: false,
      observaciones: "",
    });
  });
});
