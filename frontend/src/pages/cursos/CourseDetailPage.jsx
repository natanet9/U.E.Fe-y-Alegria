import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { getCourseDetail, updateGrades } from "../../services/coursesService";
import { markAttendance, getAttendance } from "../../services/attendanceService";
import activitiesService from "../../services/activitiesService";
import apiClient from "../../services/apiClient";
import Toast from "../../components/Toast";
import Modal from "../../components/Modal";
import { getStoredUser } from "../../services/authService";
import { useDialog } from "../../hooks/useDialog";

const EMPTY_ARRAY = [];
const EMPTY_OBJECT = {};

function normalizeText(value) {
  return (value || "").toString().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

function isAutoevaluacionDimension(dimension) {
  return normalizeText(dimension?.nombre).startsWith("autoevalu");
}



function localDate(d = new Date()) {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function CourseDetailPage() {
  const currentUser = useMemo(() => getStoredUser(), []);
  const currentRole = ((currentUser?.cargo || currentUser?.rol || (Array.isArray(currentUser?.roles) ? currentUser.roles[0] : "") || "").toLowerCase());
  const isDirector = currentRole === "director";
  const [search] = useSearchParams();
  const navigate = useNavigate();
  const docenteAsignacionId = search.get("docente_asignacion_id") || search.get("asignacion_id");
  const [periodoId, setPeriodoId] = useState("");
  const { dialog, confirm, prompt, handleConfirm, handleCancel } = useDialog();
  const [fecha] = useState(localDate());
  const [data, setData] = useState(null);
  const [attendance, setAttendance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savingAll, setSavingAll] = useState(false);
  const [tab, setTab] = useState("attendance");
  const [actividadesNotas, setActividadesNotas] = useState({});
  const [autoevaluacion, setAutoevaluacion] = useState({});
  const [nuevoActividad, setNuevoActividad] = useState({ nombre: "", puntaje_maximo: 100, dimensionId: "", fecha: localDate() });
  const [toast, setToast] = useState({ mensaje: "", tipo: "success" });
  const [autorizado, setAutorizado] = useState(false);
  const [motivoCorreccion, setMotivoCorreccion] = useState("");
  const [asistenciaAutorizada, setAsistenciaAutorizada] = useState(false);
  const [asistenciaMotivo, setAsistenciaMotivo] = useState("");
  const [calendarioAsistencia, setCalendarioAsistencia] = useState(null);
  const initialPeriodoRef = useRef(null);
  const calendarioCacheRef = useRef(new Map());
  const calendarioEnCursoRef = useRef(null);
  const [mesCalendario, setMesCalendario] = useState(() => {
    const now = new Date();
    return { year: now.getFullYear(), month: now.getMonth() + 1 };
  });
  const [fechaSeleccionada, setFechaSeleccionada] = useState("");

  const showToast = useCallback((tipo, mensaje) => {
    setToast({ mensaje, tipo });
  }, []);

  const closeToast = useCallback(() => {
    setToast({ mensaje: "", tipo: "success" });
  }, []);

  const autorizarCorreccion = async () => {
    const motivo = await prompt(
      "Como director, escribe el motivo de esta corrección para registrarlo en auditoría.",
      { iconType: "info", title: "Autorizar corrección", placeholder: "Describe el motivo..." }
    );
    if (!motivo || !motivo.trim()) return false;
    setMotivoCorreccion(motivo.trim());
    setAutorizado(true);
    showToast("success", "Edición autorizada. Los cambios quedarán registrados en auditoría.");
    return true;
  };

  const cancelarAutorizacion = () => {
    setAutorizado(false);
    setMotivoCorreccion("");
  };

  const autorizarAsistencia = async () => {
    const motivo = await prompt(
      "Como director, escribe el motivo para registrar/modificar asistencia.",
      { iconType: "info", title: "Autorizar asistencia", placeholder: "Describe el motivo..." }
    );
    if (!motivo || !motivo.trim()) return false;
    setAsistenciaMotivo(motivo.trim());
    setAsistenciaAutorizada(true);
    showToast("success", "Edición de asistencia autorizada.");
    return true;
  };

  const cancelarAutorizacionAsistencia = () => {
    setAsistenciaAutorizada(false);
    setAsistenciaMotivo("");
  };

  const cargarCalendario = useCallback(async (year, month) => {
    if (!docenteAsignacionId) return;
    const cacheKey = `${year}-${String(month).padStart(2, "0")}`;
    if (calendarioCacheRef.current.has(cacheKey)) {
      setCalendarioAsistencia(calendarioCacheRef.current.get(cacheKey));
      return;
    }
    if (calendarioEnCursoRef.current === cacheKey) return;
    calendarioEnCursoRef.current = cacheKey;
    try {
      const resp = await apiClient.get("/attendance/calendar/", {
        params: { docente_asignacion_id: docenteAsignacionId, year, month },
      });
      calendarioCacheRef.current.set(cacheKey, resp.data);
      setCalendarioAsistencia(resp.data);
    } catch {
      calendarioCacheRef.current.set(cacheKey, {});
      setCalendarioAsistencia({});
    } finally {
      calendarioEnCursoRef.current = null;
    }
  }, [docenteAsignacionId]);

  const aplicarDiaSeleccionado = useCallback((dateStr, calendario = calendarioAsistencia) => {
    const dayData = calendario?.[dateStr];
    if (!dayData || !dayData.registros || !Object.keys(dayData.registros).length) {
      setAttendance(null);
      return;
    }

    const map = {};
    Object.entries(dayData.registros).forEach(([estudianteId, estado]) => {
      map[estudianteId] = estado === "presente" ? "present" : estado === "con_licencia" ? "licencia" : "absent";
    });
    setAttendance(map);
  }, [calendarioAsistencia]);

  const seleccionarFecha = (dateStr) => {
    setFechaSeleccionada(dateStr);
    if (!dateStr) return;
    if (isDirector) aplicarDiaSeleccionado(dateStr);
  };
  const [hoveredActividad, setHoveredActividad] = useState(null);
  const [collapsedDims, setCollapsedDims] = useState({});
  const [tableZoom, setTableZoom] = useState(100);

  const estudiantes = data?.estudiantes || EMPTY_ARRAY;
  const periodos = data?.periodos || EMPTY_ARRAY;
  const dimensiones = data?.dimensiones || EMPTY_ARRAY;
  const actividades = data?.actividades || EMPTY_ARRAY;
  const notasDim = data?.notas_dimension || EMPTY_OBJECT;
  const cerrado = data?.cerrado || false;
  const activityNotes = useMemo(() => data?.actividad_notas || EMPTY_OBJECT, [data]);

  const dimensionNotes = useMemo(() => {
    const map = {};
    Object.entries(notasDim).forEach(([estudianteId, dimensiones]) => {
      map[estudianteId] = { total: 0, detalles: dimensiones };
    });
    return map;
  }, [notasDim]);

  const autoDimension = useMemo(() => dimensiones.find((dimension) => isAutoevaluacionDimension(dimension)), [dimensiones]);
  const dimensionGroups = useMemo(() => dimensiones.filter((dimension) => !isAutoevaluacionDimension(dimension)), [dimensiones]);
  const autoDimensionMax = Number(autoDimension?.puntaje_maximo ?? 5);

  const activitiesByDimension = useMemo(() => {
    const groups = {};
    dimensionGroups.forEach((dimension) => {
      groups[dimension.id] = actividades.filter((activity) => String(activity.dimension_id) === String(dimension.id));
    });
    return groups;
  }, [actividades, dimensionGroups]);

  const selectedPeriodLabel = useMemo(() => {
    const selected = periodos.find((periodo) => periodo.id === periodoId);
    return selected ? selected.nombre : "Trimestre pendiente";
  }, [periodoId, periodos]);

  useEffect(() => {
    if (!docenteAsignacionId) return;
    let mounted = true;
    setLoading(true);
    getCourseDetail({ docenteAsignacionId })
      .then((response) => {
        if (!mounted) return;
        setData(response);
        if (initialPeriodoRef.current === null) {
          const activePeriod = (response.periodos || []).find((periodo) => periodo.activo) || (response.periodos || [])[0];
          if (activePeriod) setPeriodoId(activePeriod.id);
          initialPeriodoRef.current = activePeriod?.id || null;
        }
      })
      .catch((requestError) => {
        if (!mounted) return;
        let msg = requestError?.response?.data?.error;
        if (!msg) {
          if (requestError?.code === 'ERR_CANCELED' || requestError?.message?.includes('aborted')) {
            msg = 'La solicitud tardó demasiado. Intenta de nuevo.';
          } else if (requestError?.response?.status === 403) {
            msg = 'No tienes permisos para ver este curso.';
          } else if (requestError?.response?.status === 404) {
            msg = 'El curso o asignación no fue encontrado.';
          } else {
            msg = 'No fue posible cargar el curso. Verifica la conexión e intenta de nuevo.';
          }
        }
        showToast("error", msg);
        setData(null);
      })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, [docenteAsignacionId]);

  useEffect(() => {
    if (!docenteAsignacionId || !periodoId) return;
    if (initialPeriodoRef.current === periodoId) {
      initialPeriodoRef.current = null;
      return;
    }

    let mounted = true;
    setLoading(true);
    getCourseDetail({ docenteAsignacionId, periodoId })
      .then((response) => {
        if (!mounted) return;
        setData(response);
      })
      .catch((requestError) => {
        if (!mounted) return;
        showToast("error", requestError?.response?.data?.error || "No fue posible cargar el curso");
      })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, [docenteAsignacionId, periodoId]);

  useEffect(() => {
    if (isDirector && docenteAsignacionId) {
      cargarCalendario(mesCalendario.year, mesCalendario.month);
    }
  }, [isDirector, docenteAsignacionId, mesCalendario, cargarCalendario]);

  useEffect(() => {
    if (!docenteAsignacionId || isDirector || tab !== "attendance") return;
    let mounted = true;
    const dateStr = fechaSeleccionada || fecha;
    getAttendance({ docenteAsignacionId, fecha: dateStr })
      .then((response) => {
        if (!mounted) return;
        const list = Array.isArray(response) ? response : (response?.asistencias || []);
        const map = {};
        if (list.length) {
          list.forEach((r) => {
            map[r.estudiante_id] = r.estado === "presente" ? "present" : r.estado === "con_licencia" ? "licencia" : "absent";
          });
        }
        setAttendance(map);
      })
      .catch(() => {
        if (!mounted) return;
        setAttendance({});
      });
    return () => { mounted = false; };
  }, [docenteAsignacionId, isDirector, tab, fechaSeleccionada, fecha]);

  useEffect(() => {
    if (!fechaSeleccionada) return;
    aplicarDiaSeleccionado(fechaSeleccionada);
  }, [calendarioAsistencia, fechaSeleccionada, aplicarDiaSeleccionado]);

  useEffect(() => {
    if (!docenteAsignacionId) return;
    const nextNotas = {};
    Object.entries(activityNotes || {}).forEach(([actividadId, valores]) => {
      nextNotas[actividadId] = { ...valores };
    });
    setActividadesNotas(nextNotas);
    const nextAuto = {};
    const autoActividad = actividades.find((a) =>
      normalizeText(a.dimension_nombre).startsWith("autoevalu")
    );
    if (autoActividad) {
      const autoNotas = activityNotes[autoActividad.id] || {};
      estudiantes.forEach((estudiante) => {
        nextAuto[estudiante.id] = Number(autoNotas[estudiante.id] ?? 0);
      });
    } else {
      estudiantes.forEach((estudiante) => {
        nextAuto[estudiante.id] = 0;
      });
    }
    setAutoevaluacion(nextAuto);
  }, [docenteAsignacionId, activityNotes, actividades, estudiantes]);

  useEffect(() => {
    if (!dimensionGroups.length) return;
    setNuevoActividad((current) => {
      if (current.dimensionId) return current;
      return { ...current, dimensionId: dimensionGroups[0].id };
    });
  }, [dimensionGroups]);

  const refreshCourse = async () => {
    const response = await getCourseDetail({ docenteAsignacionId, periodoId });
    setData(response);
    return response;
  };

  const toggleAttendance = (estudianteId) => {
    if (!attendance) return;
    setAttendance((current) => {
      const currentState = current[estudianteId];
      if (!currentState) return { ...current, [estudianteId]: "present" };
      const cycle = { present: "absent", absent: "licencia", licencia: "present" };
      return { ...current, [estudianteId]: cycle[currentState] };
    });
  };

  const submitAttendance = async () => {
    if (!attendance) {
      showToast("error", "No hay datos de asistencia para esta fecha");
      return;
    }
    setSaving(true);
    const estados = {};
    Object.entries(attendance).forEach(([key, value]) => { estados[key] = { present: "presente", absent: "ausente", licencia: "con_licencia" }[value] || "ausente"; });
    const fechaAsistencia = fechaSeleccionada || fecha;
    try {
      await markAttendance({ docenteAsignacionId, fecha: fechaAsistencia, estados, motivo: isDirector ? (asistenciaMotivo || undefined) : undefined });
      showToast("success", "Asistencias guardadas");
    } catch (requestError) {
      showToast("error", requestError?.response?.data?.error || "Error al guardar asistencia");
    } finally { setSaving(false); }
  };

  const handleActivityValueChange = (actividadId, estudianteId, value) => {
    setActividadesNotas((current) => ({
      ...current,
      [actividadId]: {
        ...(current[actividadId] || {}),
        [estudianteId]: value === "" ? "" : Math.max(0, Number(value)),
      },
    }));
  };

  const handleAutoevaluacionChange = (estudianteId, value) => {
    setAutoevaluacion((current) => ({
      ...current,
      [estudianteId]: value === "" ? "" : Math.max(0, Number(value)),
    }));
  };

  const getSavedDimensionValue = (estudianteId, dimensionId) => Number(dimensionNotes[estudianteId]?.detalles?.[dimensionId] ?? 0);

  const attendanceState = (estado) => {
    if (estado === "present") return { label: "Presente", className: "bg-emerald-100 text-emerald-700" };
    if (estado === "licencia") return { label: "Con licencia", className: "bg-amber-100 text-amber-700" };
    return { label: "Ausente", className: "bg-rose-100 text-rose-700" };
  };

  const getActivityValue = (actividadId, estudianteId) => {
    const currentValue = actividadesNotas[actividadId]?.[estudianteId];
    if (currentValue === undefined) return activityNotes[actividadId]?.[estudianteId] ?? "";
    return currentValue;
  };

  const getDimensionHeaderSpan = (dimension) => {
    const groupedActivities = activitiesByDimension[dimension.id] || [];
    return groupedActivities.length + 1;
  };

  const getFinalScore = (estudianteId) => {
    return dimensiones.reduce((total, dimension) => total + getDimensionScore(dimension, estudianteId), 0);
  };

  const getDimensionScore = (dimension, estudianteId) => {
    if (!dimension) return 0;
    if (autoDimension && dimension.id === autoDimension.id) {
      const draftValue = autoevaluacion[estudianteId];
      if (draftValue === "") return getSavedDimensionValue(estudianteId, dimension.id);
      return Math.max(0, Math.min(Number(draftValue || 0), autoDimensionMax));
    }
    const dimensionActivities = activitiesByDimension[dimension.id] || [];
    if (!dimensionActivities.length) return getSavedDimensionValue(estudianteId, dimension.id);
    const ratios = dimensionActivities
      .map((actividad) => {
        const value = getActivityValue(actividad.id, estudianteId);
        if (value === "" || value === null || value === undefined) return null;
        const max = Number(actividad.puntaje_maximo || 0);
        if (!max) return null;
        return Number(value) / max;
      })
      .filter((value) => value !== null);
    if (!ratios.length) return getSavedDimensionValue(estudianteId, dimension.id);
    const averageRatio = ratios.reduce((sum, value) => sum + value, 0) / ratios.length;
    const rawValue = Math.round(averageRatio * Number(dimension.puntaje_maximo || 0) * 100) / 100;
    return Math.max(0, Math.min(rawValue, Number(dimension.puntaje_maximo || 0)));
  };

  const agregarActividad = async () => {
    if (!nuevoActividad.nombre.trim()) { showToast("error", "Ingresa el nombre de la actividad"); return; }
    if (!nuevoActividad.dimensionId) { showToast("error", "Selecciona una dimensión"); return; }
    if (!nuevoActividad.fecha) { showToast("error", "Selecciona una fecha para la actividad"); return; }
    setSaving(true);
    try {
      await activitiesService.createActividad({
        docenteAsignacionId,
        nombre: nuevoActividad.nombre.trim(),
        puntaje_maximo: Number(nuevoActividad.puntaje_maximo || 100),
        dimensionId: nuevoActividad.dimensionId,
        periodoId: periodoId || periodos?.[0]?.id,
        fecha: nuevoActividad.fecha || fecha,
      });
      setNuevoActividad((current) => ({ ...current, nombre: "", puntaje_maximo: 100 }));
      await refreshCourse();
      showToast("success", "Actividad creada");
    } catch (requestError) {
      showToast("error", requestError?.response?.data?.error || "Error al crear actividad");
    } finally { setSaving(false); }
  };

  const eliminarActividad = async (actividadId) => {
    const ok = await confirm("¿Eliminar esta actividad?", { iconType: "delete", title: "Eliminar actividad" });
    if (!ok) return;
    setSaving(true);
    try {
      await activitiesService.deleteActividad({ actividadId });
      await refreshCourse();
      showToast("success", "Actividad eliminada");
    } catch (requestError) {
      showToast("error", requestError?.response?.data?.error || "Error al eliminar actividad");
    } finally { setSaving(false); }
  };

  const guardarCalificaciones = async () => {
    let motivoDirector = motivoCorreccion;
    if (isDirector) {
      if (!motivoDirector.trim()) {
        showToast("error", "Debes autorizar la corrección antes de guardar.");
        return;
      }

      const accepted = await confirm("Verifica los cambios. El motivo quedará guardado en el historial.", { iconType: "warning", title: "Confirmar cambios" });
      if (!accepted) return;
    }

    setSavingAll(true);
    try {
      const batchActividades = actividades.map((actividad) => ({
        actividad_id: actividad.id,
        notas: actividadesNotas[actividad.id] || {},
      }));

      const autoActividad = actividades.find((a) =>
        normalizeText(a.dimension_nombre).startsWith("autoevalu")
      );
      if (autoActividad) {
        const autoNotas = {};
        estudiantes.forEach((est) => {
          const val = autoevaluacion[est.id];
          if (val !== undefined && val !== null && val !== "") {
            autoNotas[est.id] = Number(val);
          }
        });
        const existingIdx = batchActividades.findIndex((b) => b.actividad_id === autoActividad.id);
        if (existingIdx >= 0) {
          batchActividades[existingIdx].notas = { ...batchActividades[existingIdx].notas, ...autoNotas };
        } else {
          batchActividades.push({ actividad_id: autoActividad.id, notas: autoNotas });
        }
      }

      await activitiesService.updateActividadesNotasBatch({ actividades: batchActividades, motivo: motivoDirector || undefined });
      await activitiesService.recomputeTrimestre({ docenteAsignacionId, periodoId });
      showToast("success", "Calificaciones guardadas");
    } catch (requestError) {
      showToast("error", requestError?.response?.data?.error || "Error al guardar calificaciones");
    } finally { setSavingAll(false); }
  };

  if (!docenteAsignacionId) return <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm font-medium text-slate-600">Asignación no especificada</div>;
  if (loading) return <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm font-medium text-slate-600">Cargando...</div>;

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(15,23,42,0.06),rgba(255,255,255,0.98),rgba(14,165,233,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">
              {data?.curso?.grado} {data?.curso?.paralelo} · {data?.curso?.nivel}
            </p>
            <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">{data?.curso?.area || "Calificaciones del trimestre"}</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">Tabla por dimensión, actividades editables, autoevaluación fija y final sobre 100 puntos.</p>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            {cerrado ? (
              <span className="rounded-2xl border border-slate-300 bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-600">🔒 Cerrado</span>
            ) : (
              <span className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-700">✓ Abierto</span>
            )}
            {!isDirector && !cerrado && (
              <button
                type="button"
                onClick={async () => {
                  const ok = await confirm("¿Estás seguro de cerrar este periodo? Una vez cerrado no podrás modificar notas. Para cambios necesitarás que el director o secretaria lo reabra.", { iconType: "warning", title: "Cerrar periodo" });
                  if (!ok) return;
                  setSaving(true);
                  try {
                    await apiClient.post("/cierre/", { accion: "cerrar", docente_asignacion_id: docenteAsignacionId, periodo_id: periodoId });
                    showToast("success", "Periodo cerrado exitosamente");
                    const response = await getCourseDetail({ docenteAsignacionId, periodoId });
                    setData(response);
                  } catch (err) {
                    showToast("error", err?.response?.data?.error || "Error al cerrar periodo");
                  } finally { setSaving(false); }
                }}
                className="rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
              >
                Cerrar periodo
              </button>
            )}
            <a
              href={`${import.meta.env.VITE_API_URL}/reports/download/?docente_asignacion_id=${docenteAsignacionId}&periodo_id=${periodoId}`}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              Exportar Excel
            </a>
            <select
              value={docenteAsignacionId || ""}
              onChange={(e) => navigate(`/cursos/detalle?docente_asignacion_id=${e.target.value}`)}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-300"
            >
              {(data?.asignaciones || []).map((asig) => (
                <option key={asig.id} value={asig.id}>
                  {asig.area} ({asig.docente})
                </option>
              ))}
            </select>
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700">{selectedPeriodLabel}</div>
          </div>
        </div>
      </header>

      <Toast mensaje={toast.mensaje} tipo={toast.tipo} onClose={closeToast} />
      <Modal
        isOpen={dialog.isOpen}
        mode={dialog.mode}
        iconType={dialog.iconType}
        title={dialog.title}
        message={dialog.message}
        inputPlaceholder={dialog.inputPlaceholder}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />

      <div className="border-b border-slate-200">
        <div className="flex gap-4">
          <button type="button" onClick={() => setTab("attendance")} className={`px-4 py-2 ${tab === "attendance" ? "border-b-2 border-blue-600 font-bold text-blue-700" : "text-slate-600"}`}>Asistencia</button>
          <button type="button" onClick={() => setTab("grades")} className={`px-4 py-2 ${tab === "grades" ? "border-b-2 border-blue-600 font-bold text-blue-700" : "text-slate-600"}`}>Notas</button>
        </div>
      </div>

      {tab === "attendance" ? (
        <div className="space-y-4">
          {isDirector ? (
            <>
              {asistenciaAutorizada ? (
                <section className="rounded-2xl border border-emerald-300 bg-emerald-50 px-5 py-4 text-sm text-emerald-900">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold">✅ Edición de asistencia autorizada</p>
                      <p className="mt-1">Motivo: {asistenciaMotivo}</p>
                    </div>
                    <button type="button" onClick={cancelarAutorizacionAsistencia} className="rounded-xl border border-emerald-300 bg-white px-4 py-2 text-xs font-semibold text-emerald-700 transition hover:bg-emerald-100">Cancelar autorización</button>
                  </div>
                </section>
              ) : (
                <section className="rounded-2xl border border-amber-300 bg-amber-50 px-5 py-4 text-sm text-amber-900">
                  <p className="font-semibold">🔒 Solo lectura — modo director</p>
                  <p className="mt-1">Selecciona un día del calendario para ver la asistencia. Para modificar, autoriza indicando el motivo.</p>
                  <button type="button" onClick={autorizarAsistencia} className="mt-3 rounded-2xl bg-amber-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-amber-700">Autorizar asistencia</button>
                </section>
              )}

              <section className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
                <div className="flex items-center justify-between mb-4">
                  <button type="button" onClick={() => setMesCalendario((m) => m.month === 1 ? { year: m.year - 1, month: 12 } : { year: m.year, month: m.month - 1 })} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">←</button>
                  <h3 className="text-lg font-black text-slate-950">
                    {new Date(mesCalendario.year, mesCalendario.month - 1).toLocaleDateString("es-PA", { month: "long", year: "numeric" })}
                  </h3>
                  <button type="button" onClick={() => setMesCalendario((m) => m.month === 12 ? { year: m.year + 1, month: 1 } : { year: m.year, month: m.month + 1 })} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">→</button>
                </div>
                <div className="grid grid-cols-7 gap-1 text-center text-xs font-semibold text-slate-500 mb-1">
                  {["Do", "Lu", "Ma", "Mi", "Ju", "Vi", "Sa"].map((d) => (<div key={d} className="py-2">{d}</div>))}
                </div>
                <div className="grid grid-cols-7 gap-1 text-center text-sm">
                  {(() => {
                    const firstDay = new Date(mesCalendario.year, mesCalendario.month - 1, 1).getDay();
                    const daysInMonth = new Date(mesCalendario.year, mesCalendario.month, 0).getDate();
                    const cells = [];
                    for (let i = 0; i < firstDay; i++) cells.push(<div key={`empty-${i}`} />);
                    for (let d = 1; d <= daysInMonth; d++) {
                      const key = `${mesCalendario.year}-${String(mesCalendario.month).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
                      const dayData = calendarioAsistencia?.[key];
                      const presente = dayData?.presente ?? 0;
                      const total = dayData?.total || estudiantes.length;
                      const isSelected = key === fechaSeleccionada;
                      cells.push(
                        <button key={key} type="button" onClick={() => seleccionarFecha(key)} className={`rounded-xl border p-2 transition hover:shadow-sm ${isSelected ? "border-blue-400 bg-blue-50 ring-2 ring-blue-200" : "border-slate-200 bg-white hover:border-slate-300"}`}>
                          <div className="text-sm font-bold text-slate-900">{d}</div>
                          {dayData ? (
                            <div className={`mt-1 text-[10px] font-semibold ${presente >= total * 0.75 ? "text-emerald-600" : presente >= total * 0.5 ? "text-amber-600" : "text-red-600"}`}>
                              {presente}/{total}
                            </div>
                          ) : (
                            <div className="mt-1 text-[10px] text-slate-300">—</div>
                          )}
                        </button>
                      );
                    }
                    return cells;
                  })()}
                </div>
              </section>

              {fechaSeleccionada ? (
                <div className="space-y-4 rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
                  <div className="flex flex-wrap items-end gap-4">
                    <div>
                      <label className="mb-2 block text-sm font-semibold text-slate-700">Fecha</label>
                      <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-700">
                        {new Date(fechaSeleccionada + "T12:00:00").toLocaleDateString("es-PA", { year: "numeric", month: "long", day: "numeric" })}
                      </div>
                    </div>
                    <div className="ml-auto">
                      <button type="button" onClick={submitAttendance} disabled={saving || !asistenciaAutorizada || !attendance} className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50">Guardar asistencia</button>
                    </div>
                  </div>
                  {!attendance ? (
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-10 text-center text-sm font-medium text-slate-500">
                      No hay datos de asistencia para esta fecha.
                    </div>
                  ) : (
                  <div className="overflow-x-auto rounded-2xl border border-slate-200">
                    <table className="min-w-full divide-y divide-slate-200">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Estudiante</th>
                        <th className="px-4 py-3 text-center text-xs font-bold uppercase tracking-wide text-slate-600">Estado</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                      {estudiantes.map((estudiante) => (
                        <tr key={estudiante.id} className="hover:bg-slate-50/80">
                          <td className="px-4 py-4">
                            <div className="flex items-center gap-3">
                              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 font-bold text-blue-700">{(estudiante.nombres || "??").split(" ").map((part) => part[0]).slice(0, 2).join("")}</div>
                                <div>
                                  <p className="text-sm font-semibold text-slate-900">{[estudiante.nombres, estudiante.primer_apellido].filter(Boolean).join(" ")}</p>
                                </div>
                            </div>
                          </td>
                          <td className="px-4 py-4 text-center">
                            {asistenciaAutorizada ? (
                              <button type="button" onClick={() => toggleAttendance(estudiante.id)} className={`inline-flex rounded-full px-4 py-2 text-sm font-semibold transition ${attendanceState(attendance[estudiante.id]).className}`}>
                                {attendanceState(attendance[estudiante.id]).label}
                              </button>
                            ) : (
                              <span className={`inline-flex rounded-full px-4 py-2 text-sm font-semibold ${attendanceState(attendance[estudiante.id]).className}`}>
                                {attendanceState(attendance[estudiante.id]).label}
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  </div>
                  )}
                </div>
              ) : (
                <div className="rounded-[1.75rem] border border-slate-200 bg-white p-10 text-center text-sm text-slate-400 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
                  Selecciona un día del calendario para ver la asistencia.
                </div>
              )}
            </>
          ) : (
            <div className="space-y-4 rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
              <div className="flex flex-wrap items-end gap-4">
                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-700">Fecha</label>
                  <input type="date" value={fechaSeleccionada || fecha} disabled className="rounded-2xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-500 outline-none cursor-not-allowed" />
                </div>
                <div className="ml-auto">
                  <button type="button" onClick={submitAttendance} disabled={saving} className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50">Guardar asistencia</button>
                </div>
              </div>
              <div className="overflow-x-auto rounded-2xl border border-slate-200">
                <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Estudiante</th>
                    <th className="px-4 py-3 text-center text-xs font-bold uppercase tracking-wide text-slate-600">Estado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {estudiantes.map((estudiante) => (
                    <tr key={estudiante.id} className="hover:bg-slate-50/80">
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 font-bold text-blue-700">{(estudiante.nombres || "??").split(" ").map((part) => part[0]).slice(0, 2).join("")}</div>
                            <div>
                              <p className="text-sm font-semibold text-slate-900">{[estudiante.nombres, estudiante.primer_apellido].filter(Boolean).join(" ")}</p>
                            </div>
                        </div>
                      </td>
                      <td className="px-4 py-4 text-center">
                        <button type="button" onClick={() => toggleAttendance(estudiante.id)} className={`inline-flex rounded-full px-4 py-2 text-sm font-semibold transition ${attendanceState(attendance?.[estudiante.id]).className}`}>
                          {attendanceState(attendance?.[estudiante.id]).label}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              </div>
            </div>
          )}
        </div>
      ) : null}

      {tab === "grades" ? (
        <div className="space-y-6">
          {isDirector ? (
            autorizado ? (
              <section className="rounded-2xl border border-emerald-300 bg-emerald-50 px-5 py-4 text-sm text-emerald-900">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold">✅ Edición autorizada</p>
                    <p className="mt-1">Motivo: {motivoCorreccion}</p>
                  </div>
                  <button type="button" onClick={cancelarAutorizacion} className="rounded-xl border border-emerald-300 bg-white px-4 py-2 text-xs font-semibold text-emerald-700 transition hover:bg-emerald-100">Cancelar autorización</button>
                </div>
              </section>
            ) : (
              <section className="rounded-2xl border border-amber-300 bg-amber-50 px-5 py-4 text-sm text-amber-900">
                <p className="font-semibold">🔒 Solo lectura — modo director</p>
                <p className="mt-1">Para modificar notas, primero autoriza la corrección indicando el motivo.</p>
                <button type="button" onClick={autorizarCorreccion} className="mt-3 rounded-2xl bg-amber-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-amber-700">Autorizar corrección</button>
              </section>
            )
          ) : null}

          {cerrado && !isDirector ? (
            <section className="rounded-2xl border border-slate-300 bg-slate-50 px-5 py-4 text-sm text-slate-700">
              <p className="font-semibold">🔒 Periodo cerrado</p>
              <p className="mt-1">Este periodo está cerrado. Las notas están en modo solo lectura. Si necesitas hacer cambios, solicita al director o secretaria que reabra el periodo.</p>
            </section>
          ) : null}

          {!isDirector && !cerrado ? (
            <section className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <h2 className="text-xl font-black text-slate-950">Nueva actividad</h2>
                  <p className="mt-1 text-sm text-slate-500">Selecciona una dimensión. La autoevaluación se mantiene como columna fija.</p>
                </div>
                <div className="flex gap-3 items-center">
                  <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-2 py-1">
                    <button onClick={() => setTableZoom(Math.max(80, tableZoom - 10))} className="rounded px-2 py-1 text-xs font-bold text-slate-600 hover:bg-white transition" title="Reducir zoom">−</button>
                    <span className="w-10 text-center text-xs font-bold text-slate-600">{tableZoom}%</span>
                    <button onClick={() => setTableZoom(Math.min(140, tableZoom + 10))} className="rounded px-2 py-1 text-xs font-bold text-slate-600 hover:bg-white transition" title="Aumentar zoom">+</button>
                  </div>
                  <button type="button" onClick={guardarCalificaciones} disabled={savingAll} className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50">Guardar trimestre</button>
                </div>
              </div>
              <div className="mt-6 grid gap-4 xl:grid-cols-[1.3fr_0.8fr_0.8fr_0.8fr_auto]">
                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-700">Actividad</label>
                  <input value={nuevoActividad.nombre} onChange={(event) => setNuevoActividad((current) => ({ ...current, nombre: event.target.value }))} placeholder="Ej: Práctica 1, Exposición, Proyecto..." className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-700">Dimensión</label>
                  <select value={nuevoActividad.dimensionId} onChange={(event) => setNuevoActividad((current) => ({ ...current, dimensionId: event.target.value }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white">
                    {dimensionGroups.map((dimension) => (<option key={dimension.id} value={dimension.id}>{dimension.nombre}</option>))}
                  </select>
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-700">Puntaje máximo</label>
                  <input type="number" min="1" value={nuevoActividad.puntaje_maximo} onChange={(event) => setNuevoActividad((current) => ({ ...current, puntaje_maximo: Number(event.target.value || 100) }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-700">Fecha</label>
                  <input type="date" value={nuevoActividad.fecha} onChange={(event) => setNuevoActividad((current) => ({ ...current, fecha: event.target.value }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
                </div>
                <div className="flex items-end">
                  <button type="button" onClick={agregarActividad} disabled={saving} className="w-full rounded-2xl border border-blue-200 bg-blue-50 px-5 py-3 text-sm font-semibold text-blue-700 transition hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50">Agregar</button>
                </div>
              </div>
            </section>
          ) : (
            <div className="flex items-center justify-between gap-3">
              <div className="flex gap-3 items-center">
                <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-2 py-1">
                  <button onClick={() => setTableZoom(Math.max(80, tableZoom - 10))} className="rounded px-2 py-1 text-xs font-bold text-slate-600 hover:bg-white transition" title="Reducir zoom">−</button>
                  <span className="w-10 text-center text-xs font-bold text-slate-600">{tableZoom}%</span>
                  <button onClick={() => setTableZoom(Math.min(140, tableZoom + 10))} className="rounded px-2 py-1 text-xs font-bold text-slate-600 hover:bg-white transition" title="Aumentar zoom">+</button>
                </div>
              </div>
              {!cerrado ? (
                <button type="button" onClick={guardarCalificaciones} disabled={savingAll || !autorizado} className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50">Guardar trimestre</button>
              ) : null}
            </div>
          )}

          <section className="overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
            <div className="overflow-x-auto overflow-y-auto" style={{ maxHeight: '60vh', zoom: `${tableZoom}%` }}>
              <table className="min-w-max border-separate border-spacing-0">
                <thead>
                  <tr>
                    <th rowSpan={2} className="sticky left-0 top-0 z-20 border-b border-r border-slate-200 bg-slate-950 px-5 py-4 text-left text-[11px] font-bold uppercase tracking-wide text-white">Estudiante</th>
                    {dimensiones.map((dimension, dimIndex) => {
                      if (autoDimension && dimension.id === autoDimension.id) {
                        return (
                          <th key={dimension.id} rowSpan={2} className="border-b border-r border-slate-200 bg-slate-50 px-4 py-3 text-center text-[10px] font-semibold text-slate-700">
                            <div className="flex items-center justify-center gap-2">
                              <span className="font-bold">{dimension.nombre}</span>
                              <span className="rounded-full bg-white px-2 py-1 text-[10px] font-bold text-slate-500">{dimension.puntaje_maximo}</span>
                              <button type="button" title="Autoevaluación: siempre incluida (5 pts)" className="ml-2 text-slate-400 hover:text-slate-600">ℹ️</button>
                            </div>
                          </th>
                        );
                      }
                      const collapsed = !!collapsedDims[dimension.id];
                      const span = collapsed ? 1 : getDimensionHeaderSpan(dimension);
                      return (
                        <th key={dimension.id} colSpan={span} className={`border-b border-r border-slate-200 bg-slate-100 px-3 py-3 text-center text-[11px] font-bold uppercase tracking-wide text-slate-700 ${dimIndex > 0 ? "border-l-4 border-slate-200" : ""}`}>
                          <div className="flex items-center justify-center gap-2">
                            <span>{dimension.nombre}</span>
                            <span className="rounded-full bg-white px-2 py-1 text-[10px] font-bold text-slate-500">{dimension.puntaje_maximo}</span>
                            <button type="button" onClick={() => setCollapsedDims((c) => ({ ...c, [dimension.id]: !c[dimension.id] }))} className="ml-2 rounded-full border bg-white px-2 py-1 text-[11px] font-semibold text-slate-600" title={collapsed ? "Expandir" : "Colapsar"}>
                              {collapsed ? "▾" : "▴"}
                            </button>
                          </div>
                        </th>
                      );
                    })}
                    <th rowSpan={2} className="border-b border-slate-200 bg-slate-950 px-5 py-4 text-center text-[11px] font-bold uppercase tracking-wide text-white">Final</th>
                  </tr>
                  <tr>
                    {dimensiones.map((dimension) => {
                      if (autoDimension && dimension.id === autoDimension.id) return null;
                      const groupedActivities = activitiesByDimension[dimension.id] || [];
                      const collapsed = !!collapsedDims[dimension.id];
                      if (collapsed) return (<th key={`collapsed-${dimension.id}`} className="border-b border-r border-slate-200 bg-white px-3 py-3 text-center text-[10px] font-semibold text-slate-500">Nota</th>);
                      const actividadHeaders = groupedActivities.map((actividad, actIndex) => (
                        <th key={actividad.id} onMouseEnter={() => setHoveredActividad(actividad.id)} onMouseLeave={() => setHoveredActividad(null)} className={`border-b border-r border-slate-200 bg-white px-3 py-3 text-center text-[10px] font-bold uppercase tracking-wide text-slate-500 ${actIndex === 0 ? "border-l-4 border-slate-200 pl-3" : ""} ${hoveredActividad === actividad.id ? "ring-2 ring-blue-100" : ""}`} title={`${actividad.nombre} — ${dimension.nombre}`}>
                          <div className="flex items-center justify-between gap-1">
                            <div className="flex flex-col items-start">
                              <span className="truncate max-w-[140px] text-[10px] font-semibold text-slate-700">{actividad.nombre}</span>
                              <span className="text-[9px] text-slate-400">{actividad.puntaje_maximo}pts · {actividad.fecha}</span>
                            </div>
                                {!isDirector && !cerrado ? (
                              <button type="button" onClick={() => eliminarActividad(actividad.id)} className="ml-1 rounded-full border border-rose-200 bg-rose-50 px-2 py-1 text-[9px] font-bold text-rose-600 transition hover:bg-rose-100" title="Eliminar">X</button>
                            ) : null}
                          </div>
                        </th>
                      ));
                      actividadHeaders.push(<th key={`total-header-${dimension.id}`} className="border-b border-r border-slate-200 bg-slate-50 px-3 py-3 text-center text-[10px] font-semibold text-slate-500">Nota</th>);
                      return actividadHeaders;
                    })}
                  </tr>
                </thead>
                <tbody>
                  {estudiantes.map((estudiante) => (
                    <tr key={estudiante.id} className="even:bg-slate-50/40 hover:bg-slate-50">
                      <td className="sticky left-0 z-10 border-b border-r border-slate-200 bg-inherit px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-emerald-100 font-bold text-emerald-700">{(estudiante.nombres || "??").split(" ").map((part) => part[0]).slice(0, 2).join("")}</div>
                          <div className="min-w-0">
                            <p className="truncate text-[11px] font-semibold text-slate-900">{[estudiante.nombres, estudiante.primer_apellido].filter(Boolean).join(" ")}</p>
                          </div>
                        </div>
                      </td>
                      {dimensiones.map((dimension) => {
                        const groupedActivities = activitiesByDimension[dimension.id] || [];
                        if (autoDimension && dimension.id === autoDimension.id) {
                          const value = autoevaluacion[estudiante.id] ?? getSavedDimensionValue(estudiante.id, dimension.id);
                          return (
                            <td key={`${dimension.id}-${estudiante.id}`} className="border-b border-r border-slate-200 bg-white px-3 py-3">
                              <div className="flex flex-col items-center gap-2">
                                <input type="number" min="0" max={autoDimensionMax} value={value} onChange={(event) => handleAutoevaluacionChange(estudiante.id, event.target.value)} readOnly={cerrado || (isDirector && !autorizado)} className={`w-20 rounded-2xl border px-3 py-2 text-center text-[11px] outline-none transition focus:border-blue-300 ${cerrado || (isDirector && !autorizado) ? "border-slate-100 bg-slate-50 text-slate-500" : "border-slate-200"}`} title="Autoevaluación" />
                                <span className="text-[9px] font-semibold text-slate-500">{getDimensionScore(dimension, estudiante.id)} / {autoDimensionMax}</span>
                              </div>
                            </td>
                          );
                        }
                        const collapsed = !!collapsedDims[dimension.id];
                        if (collapsed) {
                          return (<td key={`${dimension.id}-total-${estudiante.id}`} className="border-b border-r border-slate-200 bg-slate-50 px-4 py-3 text-center">
                            <span className="rounded-full bg-white px-3 py-1 text-[11px] font-bold text-slate-900 shadow-sm">{getDimensionScore(dimension, estudiante.id)}</span>
                          </td>);
                        }
                        return (
                          <>
                            {groupedActivities.map((actividad, actIndex) => (
                              <td key={`${actividad.id}-${estudiante.id}`} onMouseEnter={() => setHoveredActividad(actividad.id)} onMouseLeave={() => setHoveredActividad(null)} className={`border-b border-r border-slate-200 bg-white px-3 py-3 ${actIndex === 0 ? "border-l-4 border-slate-200 pl-3" : ""} ${hoveredActividad === actividad.id ? "bg-blue-50" : ""}`}>
                                <div className="flex flex-col items-center">
                                  <div className="mb-2 max-w-[140px] text-center text-[10px] font-semibold text-slate-700 truncate">{actividad.nombre}</div>
                                  <input type="number" min="0" max={actividad.puntaje_maximo} value={getActivityValue(actividad.id, estudiante.id)} onChange={(event) => handleActivityValueChange(actividad.id, estudiante.id, event.target.value)} readOnly={cerrado || (isDirector && !autorizado)} className={`w-20 rounded-xl border px-2 py-2 text-center text-[11px] outline-none transition focus:border-blue-300 ${cerrado || (isDirector && !autorizado) ? "border-slate-100 bg-slate-50 text-slate-500" : "border-slate-200"}`} title={actividad.nombre} />
                                </div>
                              </td>
                            ))}
                            <td key={`${dimension.id}-total-${estudiante.id}`} className="border-b border-r border-slate-200 bg-slate-50 px-4 py-3 text-center">
                              <span className="rounded-full bg-white px-3 py-1 text-[11px] font-bold text-slate-900 shadow-sm">{getDimensionScore(dimension, estudiante.id)}</span>
                            </td>
                          </>
                        );
                      })}
                      <td className="border-b border-slate-200 bg-slate-950 px-4 py-3 text-center text-white">
                        <span className="text-lg font-black">{getFinalScore(estudiante.id)}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h3 className="text-lg font-black text-slate-950">Actividades del trimestre</h3>
                <p className="mt-1 text-sm text-slate-500">Pasa el cursor por cada actividad para ver su nombre completo.</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-700">{actividades.length} actividades registradas</div>
            </div>
          </section>
        </div>
      ) : null}
    </section>
  );
}


export default CourseDetailPage;
