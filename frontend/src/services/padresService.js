import apiClient from "./apiClient";

/**
 * Servicio para el Portal de Padres de Familia (PWA Móvil)
 * No modifica ningún modelo en backend y consume los endpoints ya existentes.
 */

export async function getPadresDashboard() {
  const response = await apiClient.get("/dashboard/", {
    params: { force: 1 },
  });
  const data = response?.data?.dashboard || response?.data || {};
  return {
    estudiantes: data.estudiantes || [],
    total_estudiantes: Number(data.total_estudiantes || (data.estudiantes ? data.estudiantes.length : 0)),
    periodo_activo: data.periodo_activo || null,
  };
}

export async function getBoletinEstudiante(estudianteId, gestion = "") {
  if (!estudianteId) {
    throw new Error("Se requiere el ID del estudiante");
  }
  const params = { estudiante_id: estudianteId };
  if (gestion) params.gestion = gestion;

  const response = await apiClient.get("/report-card/", { params });
  return response.data;
}

export async function descargarBoletinArchivo(estudianteId, gestion = "", fmt = "docx") {
  if (!estudianteId) {
    throw new Error("Se requiere el ID del estudiante");
  }
  const params = {
    estudiante_id: estudianteId,
    fmt,
  };
  if (gestion) params.gestion = gestion;

  const response = await apiClient.get("/report-card/download/", {
    params,
    responseType: "blob",
  });
  return response;
}
