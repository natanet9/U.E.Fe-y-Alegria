import apiClient from "./apiClient";

// Simple in-memory cache for course detail responses keyed by docente_asignacion_id
const _courseDetailCache = new Map();

export async function getCoursesPage({ query = "", page = 1, pageSize = 8 } = {}) {
  const response = await apiClient.get("/courses/", {
    params: { query, page, page_size: pageSize },
  });
  return response.data;
}

export async function createCourse(payload) {
  const response = await apiClient.post("/courses/", payload);
  return response.data;
}

export async function updateCourse(id, payload) {
  const response = await apiClient.put(`/courses/${id}/`, payload);
  return response.data;
}

export async function deleteCourse(id) {
  const response = await apiClient.delete(`/courses/${id}/`);
  return response.data;
}

export async function restoreCourse(id) {
  const response = await apiClient.post(`/courses/${id}/restore/`);
  return response.data;
}

export async function getCourseDetail({ docenteAsignacionId, periodoId, fecha }) {
  if (!docenteAsignacionId) return null;

  const cacheKey = `${docenteAsignacionId}:${periodoId || ''}:${fecha || ''}`;
  if (_courseDetailCache.has(cacheKey)) {
    return _courseDetailCache.get(cacheKey);
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);
  try {
    const response = await apiClient.get("/courses/detail/", {
      params: { docente_asignacion_id: docenteAsignacionId, periodo_id: periodoId, fecha },
      signal: controller.signal,
    });
    const data = response.data;
    _courseDetailCache.set(cacheKey, data);
    return data;
  } finally {
    clearTimeout(timeout);
  }
}

export function clearCourseDetailCache() {
  _courseDetailCache.clear();
}

export async function getAsignacionesList() {
  const response = await apiClient.get("/courses/asignaciones/");
  return response.data;
}

export async function getCoursesDetails({ ids = [] } = {}) {
  if (!ids || !ids.length) return [];
  const q = `ids=${ids.join(',')}`;
  try {
    const resp = await apiClient.get(`/courses/details/?${q}`);
    return resp.data?.details || [];
  } catch (e) {
    return [];
  }
}
export async function updateGrades({ docenteAsignacionId, periodoId, notas, motivo, dimensionId }) {
  const response = await apiClient.post("/grades/update/", {
    docente_asignacion_id: docenteAsignacionId,
    periodo_id: periodoId,
    dimension_id: dimensionId,
    notas,
    motivo,
  });
  // Limpiar caché después de actualizar notas
  clearCourseDetailCache();
  return response.data;
}
