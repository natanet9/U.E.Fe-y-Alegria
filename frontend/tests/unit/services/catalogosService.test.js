import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../../src/services/apiClient", () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

import apiClient from "../../../src/services/apiClient";
import { getCatalogos, createCatalogo, updateCatalogo, deleteCatalogo } from "../../../src/services/catalogosService";

describe("catalogosService", () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it("getCatalogos consulta /catalogos/<modelo>/", async () => {
    apiClient.get.mockResolvedValue({ data: { niveles: [{ id: 1, nombre: "Primaria" }] } });
    const result = await getCatalogos("niveles");
    expect(apiClient.get).toHaveBeenCalledWith("/catalogos/niveles/");
    expect(result.niveles[0].nombre).toBe("Primaria");
  });

  it("createCatalogo hace POST a /catalogos/<modelo>/", async () => {
    apiClient.post.mockResolvedValue({ data: { mensaje: "Creado", data: { id: 1, nombre: "Nuevo" } } });
    const result = await createCatalogo("areas", { nombre: "Nuevo" });
    expect(apiClient.post).toHaveBeenCalledWith("/catalogos/areas/", { nombre: "Nuevo" });
    expect(result.mensaje).toBe("Creado");
  });

  it("updateCatalogo hace PUT a /catalogos/<modelo>/<id>/", async () => {
    apiClient.put.mockResolvedValue({ data: { data: { id: 1, nombre: "Actualizado" } } });
    const result = await updateCatalogo("niveles", 1, { nombre: "Actualizado" });
    expect(apiClient.put).toHaveBeenCalledWith("/catalogos/niveles/1/", { nombre: "Actualizado" });
    expect(result.data.nombre).toBe("Actualizado");
  });

  it("deleteCatalogo hace DELETE a /catalogos/<modelo>/<id>/", async () => {
    apiClient.delete.mockResolvedValue({ data: { ok: true } });
    const result = await deleteCatalogo("areas", 5);
    expect(apiClient.delete).toHaveBeenCalledWith("/catalogos/areas/5/");
    expect(result.ok).toBe(true);
  });
});
