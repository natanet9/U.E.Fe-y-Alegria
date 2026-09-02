import apiClient from "./apiClient";

export async function getReportsPage({ docenteAsignacionId, periodoId } = {}) {
  const response = await apiClient.get("/reports/", {
    params: {
      docente_asignacion_id: docenteAsignacionId,
      periodo_id: periodoId,
    },
  });
  return response.data;
}

export async function getReportsExportHistory({ periodoId = "", limit = 10 } = {}) {
  const response = await apiClient.get("/reports/history/", {
    params: {
      periodo_id: periodoId,
      limit,
    },
  });
  return response.data;
}

export async function downloadReportsDocument({ docenteAsignacionId, periodoId, format } = {}) {
  const response = await apiClient.get("/reports/download/", {
    params: {
      docente_asignacion_id: docenteAsignacionId,
      periodo_id: periodoId,
      fmt: format,
    },
    responseType: "blob",
  });
  return response;
}
