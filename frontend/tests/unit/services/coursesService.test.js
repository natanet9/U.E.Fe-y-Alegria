import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  getCourseDetail,
  updateGrades,
  clearCourseDetailCache,
  getCoursesDetails,
} from "../../../src/services/coursesService";
import apiClient from "../../../src/services/apiClient";

vi.mock("../../../src/services/apiClient", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe("coursesService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearCourseDetailCache();
  });

  it("getCourseDetail obtiene datos del curso", async () => {
    const mockData = {
      estudiantes: [],
      periodos: [],
    };
    apiClient.get.mockResolvedValue({ data: mockData });

    const result = await getCourseDetail({
      docenteAsignacionId: 1,
      periodoId: 2,
    });

    expect(result).toEqual(mockData);
    expect(apiClient.get).toHaveBeenCalledWith("/courses/detail/", {
      params: { docente_asignacion_id: 1, periodo_id: 2, fecha: undefined },
    });
  });

  it("updateGrades actualiza notas y limpia cache", async () => {
    apiClient.post.mockResolvedValue({ data: { success: true } });

    const result = await updateGrades({
      docenteAsignacionId: 1,
      periodoId: 2,
      notas: { 1: 85 },
    });

    expect(result).toEqual({ success: true });
    expect(apiClient.post).toHaveBeenCalledWith("/grades/update/", {
      docente_asignacion_id: 1,
      periodo_id: 2,
      notas: { 1: 85 },
      motivo: undefined,
      dimension_id: undefined,
    });
  });

  it("getCoursesDetails obtiene detalles de multiples cursos", async () => {
    const mockData = { details: [] };
    apiClient.get.mockResolvedValue({ data: mockData });

    const result = await getCoursesDetails({ ids: [1, 2] });

    expect(result).toEqual([]);
    expect(apiClient.get).toHaveBeenCalledWith("/courses/details/?ids=1,2");
  });
});
