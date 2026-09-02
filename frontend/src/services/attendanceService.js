import apiClient from "./apiClient";

export async function markAttendance({ docenteAsignacionId, fecha, estados, motivo }) {
  const payload = {
    docente_asignacion_id: docenteAsignacionId,
    fecha,
    estados,
    motivo,
  };
  const response = await apiClient.post("/attendance/", payload);
  return response.data;
}

export async function getAttendance({ docenteAsignacionId, fecha }) {
  const response = await apiClient.get("/attendance/", {
    params: { docente_asignacion_id: docenteAsignacionId, fecha },
  });
  return response.data;
}

export async function deleteAttendance(id) {
  const response = await apiClient.delete(`/attendance/${id}/`);
  return response.data;
}

export async function getAttendanceAdmin(params = {}) {
  const response = await apiClient.get("/attendance/admin/", { params });
  return response.data;
}
