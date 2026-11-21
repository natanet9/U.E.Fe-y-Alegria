import apiClient from "./apiClient";

export async function listarTutores({ query = "", page = 1, pageSize = 20 } = {}) {
  const params = {};
  if (query) params.query = query;
  if (page) params.page = page;
  if (pageSize) params.page_size = pageSize;

  const response = await apiClient.get("/tutores/", { params });
  return response.data;
}

export async function obtenerTutor(tutorId) {
  const response = await apiClient.get(`/tutores/${tutorId}/`);
  return response.data;
}

export async function generarCredencialesTutor(tutorId, email = null) {
  const body = email ? { email } : {};
  const response = await apiClient.post(`/tutores/${tutorId}/credenciales/`, body);
  return response.data;
}

export async function desvincularUsuarioTutor(tutorId) {
  const response = await apiClient.delete(`/tutores/${tutorId}/usuario/`);
  return response.data;
}
