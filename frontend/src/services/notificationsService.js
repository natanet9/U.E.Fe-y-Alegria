import apiClient from './apiClient';

export async function getNotificaciones({ no_leidas = false, page = 1, pageSize = 20 } = {}) {
  const response = await apiClient.get('/notificaciones/', {
    params: {
      no_leidas: no_leidas ? 'true' : 'false',
      page,
      page_size: pageSize,
    },
  });
  return response.data;
}

export async function marcarLeida(notificacionId) {
  const response = await apiClient.post(`/notificaciones/${notificacionId}/leer/`);
  return response.data;
}

export async function marcarTodasLeidas() {
  const response = await apiClient.post('/notificaciones/leer-todas/');
  return response.data;
}
