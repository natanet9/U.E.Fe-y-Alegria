import apiClient from './apiClient';

export async function listPeriodos({ gestion } = {}) {
  const response = await apiClient.get('/periodos/', { params: { gestion } });
  return response.data;
}

export async function createPeriodo(payload) {
  const response = await apiClient.post('/periodos/', { accion: 'crear', ...payload });
  return response.data;
}

export async function updatePeriodo(periodoId, payload) {
  const response = await apiClient.put(`/periodos/${periodoId}/`, payload);
  return response.data;
}

export async function deletePeriodo(periodoId) {
  const response = await apiClient.delete(`/periodos/${periodoId}/`);
  return response.data;
}

export async function habilitarPeriodo(periodoId) {
  const response = await apiClient.post('/periodos/', { accion: 'habilitar', periodo_id: periodoId });
  return response.data;
}

export async function cerrarPeriodo(periodoId) {
  const response = await apiClient.post('/periodos/', { accion: 'cerrar', periodo_id: periodoId });
  return response.data;
}

export async function markPeriodoEnviado(periodoId) {
  const response = await apiClient.post(`/periodos/${periodoId}/marcar-enviado/`);
  return response.data;
}
