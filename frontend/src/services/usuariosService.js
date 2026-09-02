import apiClient from "./apiClient";

export async function listarUsuarios({ roles = "", query = "", page = 1, pageSize = 10, incluirInactivos = false } = {}) {
  const response = await apiClient.get("/docentes/", {
    params: { rol: roles, query, page, page_size: pageSize, incluir_inactivos: incluirInactivos },
  });
  return response.data;
}

export async function crearUsuario(payload) {
  const body = {
    nombre: payload.nombre || "",
    apellido: payload.apellido || "",
    ci: payload.ci || "",
    email: payload.email,
    rol: payload.rol,
    password: payload.password || "123456",
  };
  const response = await apiClient.post("/docentes/", body);
  return response.data;
}

export async function actualizarUsuario(id, payload) {
  const response = await apiClient.put(`/docentes/${id}/detail/`, payload);
  return response.data;
}

export async function eliminarUsuario(id) {
  const response = await apiClient.delete(`/docentes/${id}/`);
  return response.data;
}

export async function restaurarUsuario(id) {
  const response = await apiClient.post(`/docentes/${id}/restore/`);
  return response.data;
}
