import apiClient from "./apiClient";

export async function getDimensiones(gestion) {
  const params = gestion ? { gestion } : {};
  const response = await apiClient.get("/catalogos/dimensiones/", { params });
  return response.data.data || response.data;
}

export async function crearDimension(data) {
  const response = await apiClient.post("/catalogos/dimensiones/", data);
  return response.data;
}

export async function actualizarDimension(id, data) {
  const response = await apiClient.put(`/catalogos/dimensiones/${id}/`, data);
  return response.data;
}

export async function eliminarDimension(id) {
  const response = await apiClient.delete(`/catalogos/dimensiones/${id}/`);
  return response.data;
}