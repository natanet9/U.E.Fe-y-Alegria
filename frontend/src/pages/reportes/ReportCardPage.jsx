import { useEffect, useState } from "react";
import { searchStudents } from "../../services/studentsService";
import { listPeriodos } from "../../services/periodoService";
import { getReportCard, downloadReportCard } from "../../services/reportCardService";
import Toast from "../../components/Toast";

const EMPTY_ARRAY = [];

const FULL_NAME = (s) => s ? `${s.nombres || ""} ${s.primer_apellido || ""} ${s.segundo_apellido || ""}`.trim() : "";

function ReportCardPage() {
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState(EMPTY_ARRAY);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [periodos, setPeriodos] = useState(EMPTY_ARRAY);
const [periodoId, setPeriodoId] = useState("");
const [gestion, setGestion] = useState(new Date().getFullYear());
const [generated, setGenerated] = useState(false);
const [reportData, setReportData] = useState(null);
const [generating, setGenerating] = useState(false);
const [toast, setToast] = useState({ mensaje: "", tipo: "success" });

function showToast(tipo, mensaje) {
  setToast({ mensaje, tipo });
}
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    listPeriodos()
      .then((response) => {
        const periodosList = Array.isArray(response) ? response : (response.periodos || EMPTY_ARRAY);
        setPeriodos(periodosList);
        const activo = periodosList.find((p) => p.estado === "activo");
        if (activo) {
          setPeriodoId(activo.id);
        }
      })
      .catch(() => {})
  }, []);

  const handleSearch = () => {
    if (!query.trim()) return;

    setSearching(true);
    setSelectedStudent(null);
    setGenerated(false);
    setReportData(null);

    searchStudents(query.trim())
      .then((response) => {
        const estudiantes = response.estudiantes || EMPTY_ARRAY;
        setSearchResults(estudiantes);
        if (!estudiantes.length) {
          showToast("error", "No se encontraron estudiantes con ese criterio.");
        }
      })
      .catch((requestError) => {
        showToast("error", requestError?.response?.data?.error || "Error al buscar estudiantes");
      })
      .finally(() => setSearching(false));
  };

  const handleGenerate = async () => {
    if (!selectedStudent || !periodoId) return;

    setGenerating(true);
    setGenerated(false);

    try {
      const response = await getReportCard({ estudianteId: selectedStudent.id, gestion });
      setReportData(response);
      setGenerated(true);
    } catch (requestError) {
      showToast("error", requestError?.response?.data?.error || "No fue posible generar el boletín");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadDocx = async () => {
    if (!selectedStudent || !periodoId) return;

    setDownloading(true);

    try {
      const response = await downloadReportCard({ estudianteId: selectedStudent.id, gestion, fmt: "docx" });
      const blob = new Blob([response.data], { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `boletin_${FULL_NAME(selectedStudent).replace(/\s+/g, "_")}.docx`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (requestError) {
      showToast("error", requestError?.response?.data?.error || "No fue posible descargar el boletín");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(14,165,233,0.08),rgba(255,255,255,0.94),rgba(99,102,241,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
            <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Boletín de Calificaciones</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">Genera y descarga boletines de calificaciones por estudiante y periodo.</p>
          </div>
        </div>
      </header>

      <Toast mensaje={toast.mensaje} tipo={toast.tipo} onClose={() => setToast({ mensaje: "", tipo: "success" })} />

      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <h2 className="text-xl font-black text-slate-950">Buscar Estudiante</h2>
        <div className="mt-4 flex flex-col gap-4 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <svg className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-3.5-3.5" />
            </svg>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); handleSearch(); } }}
              placeholder="Buscar por nombre, RUDE o CI..."
              className="w-full min-w-[280px] rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 text-sm outline-none transition focus:border-blue-300 focus:bg-white"
            />
          </div>
          <button type="button" onClick={handleSearch} disabled={searching} className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-bold text-white disabled:opacity-50">
            {searching ? "Buscando..." : "Buscar"}
          </button>
        </div>

        {searchResults.length ? (
          <div className="mt-5 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {searchResults.map((student) => {
              const initials = FULL_NAME(student).split(" ").map((n) => n[0]).slice(0, 2).join("").toUpperCase();

              return (
                <button
                  key={student.id}
                  type="button"
                  onClick={() => { setSelectedStudent(student); setGenerated(false); setReportData(null); }}
                  className={`rounded-3xl border p-4 text-left shadow-[0_18px_50px_rgba(15,23,42,0.05)] transition hover:shadow-md ${selectedStudent?.id === student.id ? "border-blue-300 bg-blue-50" : "border-slate-200 bg-white"}`}
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-900 text-sm font-black text-white">
                      {initials}
                    </div>
                    <div>
                      <p className="text-sm font-bold text-slate-950">{FULL_NAME(student)}</p>
                      <p className="text-xs text-slate-500">{student.rude ? `RUDE: ${student.rude}` : `CI: ${student.ci}`}</p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        ) : null}
      </section>

      {selectedStudent ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h2 className="text-xl font-black text-slate-950">Generar Boletín</h2>
              <p className="mt-1 text-sm text-slate-500">Estudiante: <span className="font-semibold text-slate-900">{FULL_NAME(selectedStudent)}</span></p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <label className="flex flex-col gap-1 text-sm font-semibold text-slate-600">
                Periodo
                <select value={periodoId} onChange={(e) => setPeriodoId(e.target.value)} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none">
                  <option value="">Seleccionar</option>
                  {periodos.filter(p => p.estado === "activo").map((p) => (
                    <option key={p.id} value={p.id}>{p.nombre}</option>
                  ))}
                </select>
              </label>
              <label className="flex flex-col gap-1 text-sm font-semibold text-slate-600">
                Gestión
                <input type="number" value={gestion} onChange={(e) => setGestion(e.target.value)} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none" />
              </label>
              <button type="button" onClick={handleGenerate} disabled={generating || !periodoId} className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-bold text-white disabled:opacity-50">
                {generating ? "Generando..." : "Generar boletín"}
              </button>
            </div>
          </div>
        </section>
      ) : null}

      {generated && reportData ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-black text-slate-950">Boletín</h2>
            <button type="button" onClick={handleDownloadDocx} disabled={downloading} className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-bold text-white disabled:opacity-50">
              {downloading ? "Descargando..." : "Descargar DOCX"}
            </button>
          </div>

          <div className="mt-6 rounded-3xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-6">
            <div className="grid gap-4 sm:grid-cols-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Estudiante</p>
                <p className="mt-1 text-lg font-black text-slate-950">
                  {reportData.estudiante?.nombres} {reportData.estudiante?.primer_apellido} {reportData.estudiante?.segundo_apellido}
                </p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Curso</p>
                <p className="mt-1 text-lg font-black text-slate-950">{reportData.curso?.nombre || "-"}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">RUDE</p>
                <p className="mt-1 text-lg font-black text-slate-950">{reportData.estudiante?.rude || "-"}</p>
              </div>
            </div>
          </div>

          <div className="mt-6 overflow-hidden rounded-2xl border border-slate-200">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Asignatura</th>
                    {(periodoId ? (reportData.periodos || []).filter(p => String(p.id) === String(periodoId)) : (reportData.periodos || [])).map((p) => (
                      <th key={p.id} className="px-4 py-3 text-center text-xs font-bold uppercase tracking-wide text-slate-600">{p.nombre}</th>
                    ))}
                    <th className="px-4 py-3 text-center text-xs font-bold uppercase tracking-wide text-slate-600">Promedio Final</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {reportData.materias?.length ? (
                    reportData.materias.map((materia, idx) => (
                      <tr key={materia.area_id || idx} className="border-b border-slate-100 last:border-b-0">
                        <td className="px-4 py-4 text-sm font-semibold text-slate-900">{materia.area}</td>
                        {(periodoId ? (reportData.periodos || []).filter(p => String(p.id) === String(periodoId)) : (reportData.periodos || [])).map((p) => {
                          const val = materia.notas_por_periodo?.[String(p.id)];
                          return (
                            <td key={p.id} className="px-4 py-4 text-center text-sm text-slate-700">
                              {val != null ? val.toFixed(2) : "-"}
                            </td>
                          );
                        })}
                        <td className="px-4 py-4 text-center text-sm font-bold text-blue-600">
                          {materia.promedio_final != null ? materia.promedio_final.toFixed(2) : "-"}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td className="px-4 py-10 text-center text-sm text-slate-500" colSpan={(periodoId ? 1 : (reportData.periodos?.length || 0)) + 2}>
                        No hay materias registradas.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-500">Promedio General</p>
              <p className="mt-2 text-3xl font-black text-slate-950">
                {reportData.promedio_general != null
                  ? reportData.promedio_general.toFixed(2)
                  : (() => {
                      const notas = reportData.materias?.filter((m) => m.promedio_final != null).map((m) => m.promedio_final) || [];
                      return notas.length ? (notas.reduce((a, b) => a + b, 0) / notas.length).toFixed(2) : "-";
                    })()}
              </p>
            </div>
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-500">Asistencia</p>
              <p className="mt-2 text-3xl font-black text-emerald-600">
                {reportData.asistencias?.length
                  ? (() => {
                      const totalPres = reportData.asistencias.reduce((s, a) => s + (a.presentes || 0), 0);
                      const totalClases = reportData.asistencias.reduce((s, a) => s + (a.total || 0), 0);
                      return totalClases ? ((totalPres / totalClases) * 100).toFixed(1) + "%" : "-";
                    })()
                  : "-"}
              </p>
            </div>
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-500">Estado</p>
              <p className="mt-2 text-3xl font-black text-slate-950">
                {(() => {
                  const notas = reportData.materias?.filter((m) => m.promedio_final != null).map((m) => m.promedio_final) || [];
                  const avg = notas.length ? notas.reduce((a, b) => a + b, 0) / notas.length : null;
                  if (avg == null) return "-";
                  return avg >= 51 ? "APROBADO" : "REPROBADO";
                })()}
              </p>
            </div>
          </div>

          {reportData.observaciones?.length ? (
            <div className="mt-6">
              <h3 className="text-lg font-black text-slate-950">Observaciones</h3>
              <div className="mt-3 space-y-2">
                {reportData.observaciones.map((obs, idx) => (
                  <div key={idx} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                    <span className="font-semibold">{obs.periodo} - {obs.area}:</span> {obs.observacion}{obs.indicador ? ` (${obs.indicador})` : ""}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </section>
      ) : null}
    </section>
  );
}

export default ReportCardPage;
