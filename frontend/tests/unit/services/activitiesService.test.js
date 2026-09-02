import { beforeEach, describe, expect, it, vi } from "vitest";
import activitiesService from "../../../src/services/activitiesService";
import apiClient from "../../../src/services/apiClient";
import { clearCourseDetailCache } from "../../../src/services/coursesService";

vi.mock("../../../src/services/apiClient", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock("../../../src/services/coursesService", () => ({
  clearCourseDetailCache: vi.fn(),
}));

describe("activitiesService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("getActividades obtiene actividades", async () => {
    const mockData = [];
    apiClient.get.mockResolvedValue({ data: mockData });

    const result = await activitiesService.getActividades({
      docenteAsignacionId: 1,
    });

    expect(result).toEqual(mockData);
    expect(apiClient.get).toHaveBeenCalledWith("/actividades/", {
      params: { docente_asignacion_id: 1 },
    });
  });

  it("createActividad crea actividad y limpia cache", async () => {
    const mockData = { id: 1 };
    apiClient.post.mockResolvedValue({ data: mockData });

    const result = await activitiesService.createActividad({
      docenteAsignacionId: 1,
      nombre: "Test",
      puntaje_maximo: 100,
      dimensionId: 2,
      periodoId: 3,
      fecha: "2026-01-01",
    });

    expect(result).toEqual(mockData);
    expect(apiClient.post).toHaveBeenCalledWith("/actividades/", {
      docente_asignacion_id: 1,
      nombre: "Test",
      puntaje_maximo: 100,
      dimension_id: 2,
      periodo_id: 3,
      fecha_actividad: "2026-01-01",
    });
    expect(clearCourseDetailCache).toHaveBeenCalled();
  });

  it("deleteActividad elimina actividad y limpia cache", async () => {
    apiClient.delete.mockResolvedValue({});

    await activitiesService.deleteActividad({ actividadId: 1 });

    expect(apiClient.delete).toHaveBeenCalledWith("/actividades/1/");
    expect(clearCourseDetailCache).toHaveBeenCalled();
  });

  it("updateActividadesNotas actualiza notas y limpia cache", async () => {
    const mockData = {};
    apiClient.post.mockResolvedValue({ data: mockData });

    const result = await activitiesService.updateActividadesNotas({
      actividadId: 1,
      notas: { 1: 85 },
    });

    expect(result).toEqual(mockData);
    expect(clearCourseDetailCache).toHaveBeenCalled();
  });

  it("updateActividadesNotasBatch actualiza notas en lote y limpia cache", async () => {
    const mockData = {};
    apiClient.post.mockResolvedValue({ data: mockData });

    const result = await activitiesService.updateActividadesNotasBatch({
      actividades: [],
    });

    expect(result).toEqual(mockData);
    expect(clearCourseDetailCache).toHaveBeenCalled();
  });
});
