import apiClient from './apiClient';

export async function getLicenciasPage({ estado = '', page = 1, pageSize = 10 } = {}) {
  const response = await apiClient.get('/licencias/', {
    params: {
      estado,
      page,
      page_size: pageSize,
    },
  });

  return response.data;
}

export async function getLicenciaDetail(licenciaId) {
  const response = await apiClient.get(`/licencias/${licenciaId}/`);
  return response.data;
}

export async function approveLicencia(licenciaId, { aceptar = true, observaciones = '' } = {}) {
  const response = await apiClient.patch('/licencias/', {
    licencia_id: licenciaId,
    aceptar,
    observaciones,
  });

  return response.data;
}