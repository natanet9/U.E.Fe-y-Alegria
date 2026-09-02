import { useEffect, useState, useCallback, useMemo } from "react";
import { downloadReportsDocument, getReportsExportHistory, getReportsPage } from "../../services/reportsService";
import { listPeriodos, markPeriodoEnviado } from "../../services/periodoService";
import { getCoursesPage } from "../../services/coursesService";
import { getConsolidado } from "../../services/reportCardService";
import { getStoredUser } from "../../services/authService";
import Toast from "../../components/Toast";

const EMPTY_ARRAY = [];

const GRADE_RANGES = [
  { label: "Excelente", min: 96, max: 100, color: "text-emerald-700 bg-emerald-50 border-emerald-200" },
  { label: "Sobresaliente", min: 84, max: 95, color: "text-blue-700 bg-blue-50 border-blue-200" },
  { label: "Bueno", min: 68, max: 83, color: "text-violet-700 bg-violet-50 border-violet-200" },
  { label: "Regular", min: 51, max: 67, color: "text-amber-700 bg-amber-50 border-amber-200" },
  { label: "Reprobado", min: 0, max: 50, color: "text-red-700 bg-red-50 border-red-200" },
];

function gradeRange(nota) {
  if (nota == null) return null;
  const n = Number(nota);
  return GRADE_RANGES.find((r) => n >= r.min && n <= r.max) || null;
}

function StatCard({ titulo, valor, detalle, acento }) {
  const toneStyles = {
    blue: "text-blue-600 bg-blue-50",
    green: "text-emerald-600 bg-emerald-50",
    violet: "text-violet-600 bg-violet-50",
    orange: "text-orange-600 bg-orange-50",
    red: "text-red-600 bg-red-50",
    amber: "text-amber-600 bg-amber-50",
  };
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-500">{titulo}</h3>
          <p className="mt-4 text-4xl font-black tracking-tight text-slate-950">{valor}</p>
          {detalle ? <p className="mt-2 text-xs font-semibold text-emerald-600">{detalle}</p> : null}
        </div>
        <div className={`rounded-2xl p-3 ${toneStyles[acento] || toneStyles.blue}`}>
          <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
        </div>
      </div>
    </article>
  );
}

function ReportesPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [marking, setMarking] = useState(false);
  const [exportHistory, setExportHistory] = useState([]);
  const [toast, setToast] = useState({ mensaje: "", tipo: "success" });

  // Selectors
  const [periodos, setPeriodos] = useState(EMPTY_ARRAY);
  const [periodoActivo, setPeriodoActivo] = useState(null);
  const [selectedPeriodoId, setSelectedPeriodoId] = useState("");
  const [selectedAsignacionId, setSelectedAsignacionId] = useState("");
  const [asignaciones, setAsignaciones] = useState(EMPTY_ARRAY);

  // Consolidado
  const [modoConsolidado, setModoConsolidado] = useState(false);
  const [consolidado, setConsolidado] = useState(null);
  const [consolidadoLoading, setConsolidadoLoading] = useState(false);

  const showToast = useCallback((tipo, mensaje) => {
    setToast({ mensaje, tipo });
  }, []);

  const closeToast = useCallback(() => {
    setToast({ mensaje: "", tipo: "success" });
  }, []);

  const periodoEnviado = Boolean(periodoActivo?.marcado_como_enviado);
  const currentUser = getStoredUser();
  const canMarkEnviado = currentUser?.rol === "director" || currentUser?.rol === "secretaria";

  // Show all periods from past gestiones; current gestion only up to active numero
  const availablePeriodos = useMemo(() => {
    if (!periodoActivo) return periodos;
    return periodos.filter((p) => p.gestion < periodoActivo.gestion || p.numero <= periodoActivo.numero);
  }, [periodos, periodoActivo]);

  const showPeriodSelector = availablePeriodos.length > 1;

  // Load periodos
  useEffect(() => {
    let mounted = true;
    listPeriodos()
      .then((resp) => {
        if (!mounted) return;
        const list = Array.isArray(resp) ? resp : (resp?.periodos || resp?.data || []);
        setPeriodos(list);
        const activo = list.find((p) => p.estado === "activo");
        if (activo) {
          setPeriodoActivo(activo);
        }
        setSelectedPeriodoId((prev) => prev || String(activo?.id || list[0]?.id || ""));
      })
      .catch(() => {});
    return () => { mounted = false; };
  }, []);

  // Load courses / asignaciones
  useEffect(() => {
    let mounted = true;
    getCoursesPage({ pageSize: 50 })
      .then((resp) => {
        if (!mounted) return;
        const cursos = resp?.cursos || [];
        const flat = [];
        for (const c of cursos) {
          const cursoLabel = `${c.nivel || ""} ${c.grado || ""} ${c.paralelo || ""}`.trim();
          for (const a of c.asignaciones || []) {
            flat.push({
              ...a,
              cursoLabel,
              cursoId: c.id,
              label: `${a.area} — ${cursoLabel}`,
            });
          }
        }
        setAsignaciones(flat);
        if (flat.length) {
          setSelectedAsignacionId((prev) => prev || String(flat[0].id));
        }
      })
      .catch(() => {});
    return () => { mounted = false; };
  }, []);

  // Fetch reports data when selection changes
  useEffect(() => {
    if (!selectedAsignacionId || !selectedPeriodoId) return;
    let mounted = true;
    setLoading(true);

    Promise.all([
      getReportsPage({ docenteAsignacionId: selectedAsignacionId, periodoId: selectedPeriodoId }),
      getReportsExportHistory({ periodoId: selectedPeriodoId, limit: 8 }),
    ])
      .then(([response, history]) => {
        if (!mounted) return;
        setData(response);
        setExportHistory(history?.exports || []);
      })
      .catch((requestError) => {
        if (!mounted) return;
        showToast("error", requestError?.response?.data?.error || "No fue posible cargar los reportes");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => { mounted = false; };
  }, [selectedAsignacionId, selectedPeriodoId]);

  const statCards = useMemo(() => {
    if (!data) return EMPTY_ARRAY;
    const totales = data.totales || EMPTY_ARRAY;
    const totalStudents = totales.length;
    const counts = { Excelente: 0, Sobresaliente: 0, Bueno: 0, Regular: 0, Reprobado: 0 };
    let sum = 0;
    for (const t of totales) {
      const n = Number(t.nota_total) || 0;
      sum += n;
      const range = gradeRange(n);
      if (range) counts[range.label]++;
    }
    const avg = totalStudents ? (sum / totalStudents).toFixed(1) : "—";
    const passed = totalStudents - counts.Reprobado;
    return [
      { titulo: "Estudiantes", valor: totalStudents, detalle: "Matriculados", acento: "blue" },
      { titulo: "Aprobados", valor: passed, detalle: `${totalStudents ? ((passed / totalStudents) * 100).toFixed(0) : 0}% del curso`, acento: "green" },
      { titulo: "Reprobados", valor: counts.Reprobado, detalle: `${totalStudents ? ((counts.Reprobado / totalStudents) * 100).toFixed(0) : 0}% del curso`, acento: "red" },
      { titulo: "Promedio general", valor: avg, detalle: "Nota promedio", acento: "violet" },
    ];
  }, [data]);

  const gradeDistribution = useMemo(() => {
    if (!data) return EMPTY_ARRAY;
    const totales = data.totales || EMPTY_ARRAY;
    const counts = { Excelente: 0, Sobresaliente: 0, Bueno: 0, Regular: 0, Reprobado: 0 };
    for (const t of totales) {
      const n = Number(t.nota_total) || 0;
      const range = gradeRange(n);
      if (range) counts[range.label]++;
    }
    return GRADE_RANGES.map((r) => ({
      ...r,
      count: counts[r.label],
      percent: totales.length ? ((counts[r.label] / totales.length) * 100).toFixed(0) : 0,
    }));
  }, [data]);

  const handleDownload = async (format) => {
    if (!selectedAsignacionId || !selectedPeriodoId) return;
    try {
      setDownloading(true);
      const response = await downloadReportsDocument({
        docenteAsignacionId: selectedAsignacionId,
        periodoId: selectedPeriodoId,
        format,
      });
      const blob = new Blob([response.data], {
        type: response.headers["content-type"] || "application/octet-stream",
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      const contentDisposition = response.headers["content-disposition"] || "";
      const fileNameMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
      link.href = url;
      link.download = fileNameMatch ? fileNameMatch[1] : `reporte_${selectedAsignacionId}.${format === "docx" ? "docx" : "xlsx"}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (downloadError) {
      showToast("error", downloadError?.response?.data?.error || "No fue posible descargar el reporte");
    } finally {
      setDownloading(false);
    }
  };

  const handleMarkEnviado = async () => {
    if (!periodoActivo) return;
    try {
      setMarking(true);
      await markPeriodoEnviado(periodoActivo.id);
      setPeriodoActivo((prev) => ({ ...prev, marcado_como_enviado: true }));
      showToast("success", "Periodo marcado como enviado");
    } catch (e) {
      showToast("error", "No fue posible marcar el periodo");
    } finally {
      setMarking(false);
    }
  };

  // Student detail table
  const studentsWithGrades = useMemo(() => {
    if (!data) return EMPTY_ARRAY;
    const totales = data.totales || EMPTY_ARRAY;
    const dimensionMap = {};
    for (const d of data.detalle || EMPTY_ARRAY) {
      if (!dimensionMap[d.estudiante_id]) dimensionMap[d.estudiante_id] = {};
      dimensionMap[d.estudiante_id][d.dimension_nombre] = d.nota;
    }
    return totales.map((t) => ({
      estudianteId: t.estudiante_id,
      estudianteNombre: t.estudiante_nombre || `ID ${t.estudiante_id}`,
      rude: t.rude || "",
      ci: t.ci || "",
      notaTotal: t.nota_total,
      dimensiones: dimensionMap[t.estudiante_id] || {},
      asistenciaPresente: t.asistencia_presente ?? null,
      asistenciaAusente: t.asistencia_ausente ?? null,
      asistenciaLicencia: t.asistencia_licencia ?? null,
      asistenciaTotalDias: t.asistencia_total_dias ?? null,
      asistenciaPorcentaje: t.asistencia_porcentaje ?? null,
    }));
  }, [data]);

  return (
    <section className="space-y-6">
      <Toast mensaje={toast.mensaje} tipo={toast.tipo} onClose={closeToast} />
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(99,102,241,0.08),rgba(255,255,255,0.94),rgba(14,165,233,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
            <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Reportes</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">
              {selectedAsignacionId && asignaciones.length
                ? `Reporte de ${asignaciones.find((a) => String(a.id) === selectedAsignacionId)?.label || ""}`
                : "Análisis y estadísticas del desempeño académico"}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            {canMarkEnviado && periodoActivo ? (
              <div className={`rounded-2xl border px-4 py-3 text-sm font-semibold ${periodoEnviado ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-slate-200 bg-white text-slate-700"}`}>
                {periodoEnviado ? "Periodo marcado como enviado" : "Periodo no marcado como enviado"}
              </div>
            ) : null}
            <label className="flex flex-col gap-1 text-xs font-semibold text-slate-500">
              Curso / Área
              <select
                value={selectedAsignacionId}
                onChange={(e) => setSelectedAsignacionId(e.target.value)}
                className="min-w-56 rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-900 outline-none transition focus:border-slate-950"
              >
                <option value="">Selecciona un curso</option>
                {asignaciones.map((a) => (
                  <option key={a.id} value={String(a.id)}>{a.label}</option>
                ))}
              </select>
            </label>
            {showPeriodSelector ? (
              <label className="flex flex-col gap-1 text-xs font-semibold text-slate-500">
                Periodo
                <select
                  value={selectedPeriodoId}
                  onChange={(e) => setSelectedPeriodoId(e.target.value)}
                  className="min-w-44 rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-900 outline-none transition focus:border-slate-950"
                >
                  {availablePeriodos.map((p) => (
                    <option key={p.id} value={String(p.id)}>{p.nombre} {p.gestion}</option>
                  ))}
                </select>
              </label>
            ) : null}
            <div className="flex gap-2">
              <button
                type="button"
                onClick={async () => {
                  setModoConsolidado(!modoConsolidado);
                  if (!modoConsolidado) {
                    setConsolidadoLoading(true);
                    try {
                      const res = await getConsolidado();
                      setConsolidado(res);
                    } catch {
                      setToast({ mensaje: "Error al cargar consolidado", tipo: "error" });
                    } finally {
                      setConsolidadoLoading(false);
                    }
                  }
                }}
                disabled={consolidadoLoading}
                className={`rounded-2xl px-4 py-3 text-sm font-bold shadow-lg transition disabled:opacity-70 ${
                  modoConsolidado
                    ? "bg-indigo-600 text-white shadow-indigo-200 hover:bg-indigo-700"
                    : "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
                }`}
              >
                {consolidadoLoading ? "..." : modoConsolidado ? "Vista Curso" : "Vista Consolidado"}
              </button>
              <button type="button" onClick={() => handleDownload("xlsx")} disabled={downloading || !selectedAsignacionId || !selectedPeriodoId} className="rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-emerald-200 transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-70">
                {downloading ? "..." : "Excel"}
              </button>
              <button type="button" onClick={() => handleDownload("docx")} disabled={downloading || !selectedAsignacionId || !selectedPeriodoId} className="rounded-2xl bg-slate-950 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-slate-200 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70">
                {downloading ? "..." : "Descargar informe"}
              </button>
              {canMarkEnviado ? (
                <button type="button" onClick={handleMarkEnviado} disabled={marking || !periodoActivo} className="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
                  {marking ? "Marcando..." : "Marcar como enviado"}
                </button>
              ) : null}
            </div>
          </div>
        </div>
      </header>

      {modoConsolidado ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <h2 className="text-xl font-black text-slate-950">Boletín Consolidado</h2>
          <p className="mt-1 mb-4 text-sm text-slate-500">
            Promedios de todos los estudiantes agrupados por curso para la gestión {consolidado?.gestion || ""}
          </p>
          {consolidadoLoading ? (
            <div className="flex items-center justify-center py-10">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-indigo-600" />
            </div>
          ) : consolidado?.cursos?.length ? (
            <div className="space-y-6">
              {consolidado.cursos.map((curso) => (
                <div key={curso.curso_id} className="rounded-2xl border border-slate-100 p-4">
                  <h3 className="text-base font-bold text-slate-900 mb-3">{curso.curso}</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-200 text-left text-xs font-semibold uppercase text-slate-500">
                          <th className="px-3 py-2">Estudiante</th>
                          {consolidado.periodos?.map((p) => (
                            <th key={p.id} className="px-3 py-2 text-center">{p.nombre}</th>
                          ))}
                          <th className="px-3 py-2 text-center">Prom. General</th>
                        </tr>
                      </thead>
                      <tbody>
                        {curso.estudiantes?.map((est) => (
                          <tr key={est.estudiante_id} className="border-b border-slate-100 hover:bg-slate-50">
                            <td className="px-3 py-2 font-medium text-slate-900">
                              {est.nombres} {est.primer_apellido} {est.segundo_apellido || ""}
                            </td>
                            {consolidado.periodos?.map((p) => (
                              <td key={p.id} className="px-3 py-2 text-center text-slate-700">
                                {est.promedios_por_periodo?.[String(p.id)] ?? "—"}
                              </td>
                            ))}
                            <td className="px-3 py-2 text-center font-bold text-slate-900">
                              {est.promedio_general ?? "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {(!curso.estudiantes || curso.estudiantes.length === 0) && (
                    <p className="py-4 text-center text-sm text-slate-500">Sin estudiantes</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="py-10 text-center text-sm text-slate-500">
              {consolidado ? "No hay datos para esta gestión" : "Haga clic en 'Vista Consolidado' para cargar los datos."}
            </p>
          )}
        </section>
      ) : selectedAsignacionId && selectedPeriodoId ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {loading
              ? Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-36 animate-pulse rounded-3xl bg-slate-200" />)
              : statCards.map((item) => <StatCard key={item.titulo} {...item} />)}
          </div>

          {/* Grade distribution */}
          {!loading && data ? (
            <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
              <h2 className="text-xl font-black text-slate-950">Distribución de notas</h2>
              <p className="mt-1 mb-4 text-sm text-slate-500">Cantidad de estudiantes por rango de calificación</p>
              <div className="grid gap-3 sm:grid-cols-5">
                {gradeDistribution.map((r) => (
                  <div key={r.label} className={`rounded-2xl border px-4 py-4 ${r.color}`}>
                    <p className="text-3xl font-black">{r.count}</p>
                    <p className="text-sm font-semibold">{r.label}</p>
                    <p className="text-xs opacity-70">{r.percent}%</p>
                  </div>
                ))}
              </div>
            </section>
          ) : null}

          {/* Student detail table */}
          {!loading && data ? (
            <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
              <h2 className="text-xl font-black text-slate-950">Detalle de notas por estudiante</h2>
              <p className="mt-1 mb-4 text-sm text-slate-500">Notas por dimensión y total</p>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-left text-xs font-semibold uppercase text-slate-500">
                      <th className="px-3 py-2">#</th>
                      <th className="px-3 py-2">Estudiante</th>
                      <th className="px-3 py-2 text-center">SER</th>
                      <th className="px-3 py-2 text-center">SABER</th>
                      <th className="px-3 py-2 text-center">HACER</th>
                      <th className="px-3 py-2 text-center">AUTOEV.</th>
                      <th className="px-3 py-2 text-center">TOTAL</th>
                      <th className="px-3 py-2 text-center">Rango</th>
                      <th className="px-3 py-2 text-center">Asistencia</th>
                    </tr>
                  </thead>
                  <tbody>
                    {studentsWithGrades.map((s, i) => {
                      const range = gradeRange(s.notaTotal);
                      const asistenciaPct = s.asistenciaPorcentaje;
                      const attColor = asistenciaPct >= 80 ? "text-emerald-600" : asistenciaPct >= 60 ? "text-amber-600" : "text-red-600";
                      return (
                        <tr key={s.estudianteId} className="border-b border-slate-100 transition hover:bg-slate-50">
                          <td className="px-3 py-2 text-slate-400">{i + 1}</td>
                          <td className="px-3 py-2 font-medium text-slate-900">{s.estudianteNombre}</td>
                          <td className="px-3 py-2 text-center text-slate-700">{s.dimensiones?.SER ?? "—"}</td>
                          <td className="px-3 py-2 text-center text-slate-700">{s.dimensiones?.SABER ?? "—"}</td>
                          <td className="px-3 py-2 text-center text-slate-700">{s.dimensiones?.HACER ?? "—"}</td>
                          <td className="px-3 py-2 text-center text-slate-700">{s.dimensiones?.AUTOEVALUACION ?? "—"}</td>
                          <td className="px-3 py-2 text-center font-bold text-slate-900">{s.notaTotal ?? "—"}</td>
                          <td className="px-3 py-2 text-center">
                            {range ? (
                              <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-bold ${range.color}`}>
                                {range.label}
                              </span>
                            ) : "—"}
                          </td>
                          <td className="px-3 py-2 text-center">
                            {asistenciaPct != null ? (
                              <span className={`font-bold ${attColor}`}>
                                {asistenciaPct}%
                              </span>
                            ) : "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>
          ) : null}
        </>
      ) : (
        <div className="rounded-[2rem] border border-dashed border-slate-200 bg-slate-50 px-6 py-16 text-center text-sm text-slate-500">
          Selecciona un curso/área y un periodo para ver los reportes.
        </div>
      )}

      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-black text-slate-950">Historial de exportaciones</h2>
            <p className="mt-1 text-sm text-slate-500">Exportaciones recientes usadas para el envío manual interno</p>
          </div>
        </div>
        <div className="mt-6 grid gap-3 lg:grid-cols-2">
          {exportHistory.length ? exportHistory.map((item) => (
            <article key={item.id} className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-bold text-slate-950">{item.formato?.toUpperCase()} · {item.periodo || "Periodo"}</p>
                  <p className="mt-1 text-xs text-slate-500">{item.usuario} · {item.creado_en}</p>
                </div>
                <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600">{item.gestion || ""}</span>
              </div>
            </article>
          )) : (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-sm text-slate-500 lg:col-span-2">
              Aún no hay exportaciones registradas.
            </div>
          )}
        </div>
      </section>
    </section>
  );
}

export default ReportesPage;
