import apiClient from "./apiClient";

export async function getDocentesPage({ query = "", page = 1, pageSize = 8, incluirInactivos = false } = {}) {
  const response = await apiClient.get("/docentes/", {
    params: { query, rol: "docente", page, page_size: pageSize, incluir_inactivos: incluirInactivos },
  });
  return response.data;
}

export async function getDocenteDetail(id) {
  const response = await apiClient.get(`/docentes/${id}/detail/`);
  return response.data;
}

export async function createDocente(payload) {
  const body = {
    nombre: payload.nombres || payload.nombre,
    primer_apellido: payload.primer_apellido || "",
    ci: payload.ci,
    email: payload.email || `${(payload.nombres || "").toLowerCase().replace(/\s+/g, ".")}.${(payload.primer_apellido || "").toLowerCase()}@uepanama`,
    rol: payload.rol || "docente",
    password: payload.password || "123456",
  };
  if (payload.titulo_academico) body.titulo_academico = payload.titulo_academico;
  if (payload.especialidad) body.especialidad = payload.especialidad;
  if (payload.fecha_ingreso_institucion) body.fecha_ingreso_institucion = payload.fecha_ingreso_institucion;
  if (payload.anos_experiencia) body.anos_experiencia = Number(payload.anos_experiencia);
  const response = await apiClient.post("/docentes/", body);
  return response.data;
}

export async function updateDocente(id, payload) {
  const response = await apiClient.put(`/docentes/${id}/detail/`, payload);
  return response.data;
}

export async function deleteDocente(id) {
  const response = await apiClient.delete(`/docentes/${id}/`);
  return response.data;
}

export async function restoreDocente(id) {
  const response = await apiClient.post(`/docentes/${id}/restore/`);
  return response.data;
}
