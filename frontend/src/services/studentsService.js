import apiClient from "./apiClient";

export async function getStudentsPage({ query = "", gradoId = "", page = 1, pageSize = 8, incluirInactivos = false } = {}) {
  const response = await apiClient.get("/students/", {
    params: {
      query,
      grado_id: gradoId,
      page,
      page_size: pageSize,
      incluir_inactivos: incluirInactivos,
    },
  });

  return response.data;
}

export async function createStudent(payload) {
  const response = await apiClient.post("/students/", payload);
  return response.data;
}

export async function searchStudents(query) {
  const response = await apiClient.get("/students/", {
    params: { query, page_size: 20 },
  });
  return response.data;
}

export async function getStudentDetail(id) {
  const response = await apiClient.get(`/students/${id}/detail/`);
  return response.data;
}

export async function updateStudent(id, data) {
  const response = await apiClient.put(`/students/${id}/detail/`, data);
  return response.data;
}

export async function deleteStudent(id) {
  const response = await apiClient.delete(`/students/${id}/`);
  return response.data;
}

export async function restoreStudent(id) {
  const response = await apiClient.post(`/students/${id}/restore/`);
  return response.data;
}

export async function downloadStudentsExport({ format = "xlsx", gradoId = "", gestion = "", incluirInactivos = false } = {}) {
  const response = await apiClient.get("/students/export/", {
    params: { format, grado_id: gradoId || undefined, gestion: gestion || undefined, incluir_inactivos: incluirInactivos || undefined },
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", `estudiantes.${format}`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

