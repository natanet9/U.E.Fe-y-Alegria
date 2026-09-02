import apiClient from "./apiClient";

let _cache = null;
let _inFlight = null;

let _cacheCards = null;
let _inFlightCards = null;

export async function getDashboardCards({ force = false } = {}) {
  if (!force && _cacheCards) {
    return _cacheCards;
  }

  if (!force && _inFlightCards) {
    return _inFlightCards;
  }

  const req = apiClient.get("/dashboard/", {
    params: { ...(force ? { force: 1 } : {}), section: 'cards' },
  }).then((response) => {
    const payload = response?.data?.dashboard ?? response?.data ?? {};
    const normalized = {
      stats: payload.stats || { total_estudiantes: 0, total_docentes: 0, total_asignaciones: 0, periodos_activos: 0 },
      licencias_pendientes: Number(payload.licencias_pendientes || 0),
      periodo_activo: payload.periodo_activo || null,
    };
    _cacheCards = normalized;
    return normalized;
  }).finally(() => {
    _inFlightCards = null;
  });

  if (!force) {
    _inFlightCards = req;
  }

  return req;
}

export async function getDashboardData({ force = false } = {}) {
  if (!force && _cache) {
    return _cache;
  }

  if (!force && _inFlight) {
    return _inFlight;
  }

  const request = apiClient.get("/dashboard/", {
    params: force ? { force: 1 } : undefined,
  }).then((response) => {
    // normalize payload: some backends return { dashboard: {...} }, others return {...}
    const payload = response?.data?.dashboard ?? response?.data ?? {};

    // If backend returned a simple status payload (eg. { ok: true }), return it as-is
    if (payload && typeof payload === "object" && Object.prototype.hasOwnProperty.call(payload, "ok")) {
      return payload;
    }

    const normalized = {
      stats: payload.stats || {
        total_estudiantes: 0,
        total_docentes: 0,
        total_asignaciones: 0,
        periodos_activos: 0,
      },
      asistencia_semanal: payload.asistencia_semanal || { labels: [], data: [] },
      promedio_por_asignatura: payload.promedio_por_asignatura || { labels: [], data: [] },
      promedio_por_curso: payload.promedio_por_curso || { labels: [], data: [] },
      asistencia_por_curso: payload.asistencia_por_curso || { labels: [], data: [] },
      rendimiento: payload.rendimiento || [],
      estudiantes_destacados: payload.estudiantes_destacados || [],
      estudiantes_riesgo: payload.estudiantes_riesgo || [],
      estudiantes_con_notas: Number(payload.estudiantes_con_notas || 0),
      alertas: payload.alertas || [],
      ultimos_usuarios: payload.ultimos_usuarios || [],
      config_checklist: payload.config_checklist || { items: [], completados: 0, total: 0 },
      licencias_pendientes: Number(payload.licencias_pendientes || 0),
      periodo_activo: payload.periodo_activo || null,
      docentes_sin_cierre: payload.docentes_sin_cierre || [],
      asignaciones: payload.asignaciones || [],
    };

    _cache = normalized;
    return normalized;
  }).finally(() => {
    _inFlight = null;
  });

  if (!force) {
    _inFlight = request;
  }

  return request;
}

export function clearDashboardCache() {
  _cache = null;
  _inFlight = null;
  _cacheCards = null;
  _inFlightCards = null;
}
