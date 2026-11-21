import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../../src/services/apiClient", () => ({
  default: { get: vi.fn() },
}));

import apiClient from "../../../src/services/apiClient";
import {
  getPadresDashboard,
  getBoletinEstudiante,
  descargarBoletinArchivo,
} from "../../../src/services/padresService";

describe("padresService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("getPadresDashboard consulta /dashboard/ con params force=1", async () => {
    apiClient.get.mockResolvedValue({
      data: {
        dashboard: {
          estudiantes: [{ id: 1, nombres: "Lucas", primer_apellido: "Mendoza" }],
          total_estudiantes: 1,
          periodo_activo: { id: 2, nombre: "2do Trimestre" },
        },
      },
    });

    const result = await getPadresDashboard();
    expect(apiClient.get).toHaveBeenCalledWith("/dashboard/", {
      params: { force: 1 },
    });
    expect(result.estudiantes.length).toBe(1);
    expect(result.total_estudiantes).toBe(1);
    expect(result.periodo_activo.nombre).toBe("2do Trimestre");
  });

  it("getBoletinEstudiante consulta /report-card/ con estudiante_id y gestion opcional", async () => {
    apiClient.get.mockResolvedValue({
      data: {
        estudiante: { id: 5, nombres: "Ana" },
        materias: [{ area: "Matemática", promedio_final: 85 }],
      },
    });

    const result = await getBoletinEstudiante(5, "2026");
    expect(apiClient.get).toHaveBeenCalledWith("/report-card/", {
      params: { estudiante_id: 5, gestion: "2026" },
    });
    expect(result.estudiante.nombres).toBe("Ana");
  });

  it("getBoletinEstudiante lanza error si no se pasa estudianteId", async () => {
    await expect(getBoletinEstudiante(null)).rejects.toThrow("Se requiere el ID del estudiante");
  });

  it("descargarBoletinArchivo consulta /report-card/download/ con responseType blob", async () => {
    apiClient.get.mockResolvedValue({ data: new Blob(), headers: {} });
    const result = await descargarBoletinArchivo(5, "2026", "docx");
    expect(apiClient.get).toHaveBeenCalledWith("/report-card/download/", {
      params: { estudiante_id: 5, fmt: "docx", gestion: "2026" },
      responseType: "blob",
    });
    expect(result.data).toBeInstanceOf(Blob);
  });
});
