import apiClient from "./apiClient";
import { clearCourseDetailCache } from "./coursesService";

const activitiesService = {
  getActividades: async ({ docenteAsignacionId }) => {
    const response = await apiClient.get("/actividades/", {
      params: { docente_asignacion_id: docenteAsignacionId },
    });
    return response.data;
  },

  createActividad: async ({ docenteAsignacionId, nombre, puntaje_maximo, dimensionId, periodoId, fecha }) => {
    const response = await apiClient.post("/actividades/", {
      docente_asignacion_id: docenteAsignacionId,
      nombre,
      puntaje_maximo,
      dimension_id: dimensionId,
      periodo_id: periodoId,
      fecha_actividad: fecha,
    });
    clearCourseDetailCache();
    return response.data;
  },

  deleteActividad: async ({ actividadId }) => {
    const response = await apiClient.delete(`/actividades/${actividadId}/`);
    clearCourseDetailCache();
    return response.data;
  },

  updateActividadesNotas: async ({ actividadId, notas, motivo }) => {
    const response = await apiClient.post("/actividades/notas/", {
      actividad_id: actividadId,
      notas,
      motivo,
    });
    clearCourseDetailCache();
    return response.data;
  },

  updateActividadesNotasBatch: async ({ actividades, motivo }) => {
    const response = await apiClient.post("/actividades/notas/batch/", {
      actividades,
      motivo,
    });
    clearCourseDetailCache();
    return response.data;
  },

  getActividadesNotas: async ({ docenteAsignacionId }) => {
    const response = await apiClient.get("/actividades/notas-estudiante/", {
      params: { docente_asignacion_id: docenteAsignacionId },
    });
    return response.data;
  },

  recomputeTrimestre: async ({ docenteAsignacionId, periodoId }) => {
    const response = await apiClient.post("/grades/recompute-actividades/", {
      docente_asignacion_id: docenteAsignacionId,
      periodo_id: periodoId,
    });
    return response.data;
  },
};

export default activitiesService;
