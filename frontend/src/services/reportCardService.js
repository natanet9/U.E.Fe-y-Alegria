import apiClient from "./apiClient";

export async function getReportCard({ estudianteId = "", gestion = "" } = {}) {
  const response = await apiClient.get("/report-card/", {
    params: {
      estudiante_id: estudianteId,
      gestion,
    },
  });
  return response.data;
}

export async function getConsolidado(gestion) {
  const params = {};
  if (gestion) params.gestion = gestion;
  const response = await apiClient.get("/report-card/consolidado/", { params });
  return response.data;
}

export async function downloadReportCard({ estudianteId = "", gestion = "", fmt = "pdf" } = {}) {
  const response = await apiClient.get("/report-card/download/", {
    params: {
      estudiante_id: estudianteId,
      gestion,
      fmt,
    },
    responseType: "blob",
  });
  return response;
}
