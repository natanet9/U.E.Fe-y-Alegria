import apiClient from "./apiClient";

export async function cerrarDocente(docenteAsignacionId, periodoId) {
  const response = await apiClient.post("/cierre/", {
    accion: "cerrar",
    docente_asignacion_id: docenteAsignacionId,
    periodo_id: periodoId,
  });
  return response.data;
}

export async function reabrirDocente(docenteAsignacionId, periodoId) {
  const response = await apiClient.post("/cierre/", {
    accion: "reabrir",
    docente_asignacion_id: docenteAsignacionId,
    periodo_id: periodoId,
  });
  return response.data;
}
