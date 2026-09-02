import apiClient from "./apiClient";

export async function getGradesPage({ query = "", periodoId = "", page = 1, pageSize = 10 } = {}) {
  const params = { query, page, page_size: pageSize };
  if (periodoId) {
    params.periodo_id = periodoId;
  }
  const response = await apiClient.get("/grades/page/", { params });

  return response.data;
}

export async function getGradesByCourse() {
  const response = await apiClient.get("/grades/page/", {
    params: { by_course: "true" },
  });

  return response.data;
}

export async function getDocenteStatus(periodoId) {
  const params = {};
  if (periodoId) params.periodo_id = periodoId;
  const response = await apiClient.get("/grades/docente-status/", { params });
  return response.data;
}
