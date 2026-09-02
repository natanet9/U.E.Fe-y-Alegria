import { useEffect, useMemo, useState } from "react";
import BarChartMock from "../../components/charts/BarChartMock";
import { getGradesPage } from "../../services/gradesService";
import Toast from "../../components/Toast";

const EMPTY_ARRAY = [];

function StatCard({ item }) {
  const styles = {
    blue: "text-blue-600 bg-blue-50",
    violet: "text-violet-600 bg-violet-50",
    green: "text-emerald-600 bg-emerald-50",
    orange: "text-orange-600 bg-orange-50",
  };

  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
      <h3 className="text-sm font-semibold text-slate-500">{item.titulo}</h3>
      <p className="mt-4 text-4xl font-black tracking-tight text-slate-950">{item.valor}</p>
      <p className="mt-2 text-sm text-slate-500">{item.detalle}</p>
      <div className={`mt-4 inline-flex rounded-2xl px-3 py-2 text-xs font-semibold ${styles[item.acento] || styles.blue}`}>
        {item.titulo}
      </div>
    </article>
  );
}

function SectionShell({ title, description, children, extra }) {
  return (
    <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-xl font-black text-slate-950">{title}</h2>
          {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
        </div>
        {extra}
      </div>
      <div className="mt-6">{children}</div>
    </section>
  );
}

function TabButton({ active, children, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-2xl px-4 py-2 text-sm font-semibold transition ${active ? "bg-white text-slate-950 shadow-sm" : "text-slate-600 hover:text-slate-950"}`}
    >
      {children}
    </button>
  );
}

function StudentBadge({ value }) {
  if (value === "up") {
    return <span className="inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">En ascenso</span>;
  }

  if (value === "stable") {
    return <span className="inline-flex rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-700">Estable</span>;
  }

  return <span className="inline-flex rounded-full bg-orange-50 px-3 py-1 text-xs font-bold text-orange-700">Requiere apoyo</span>;
}

function CourseDistribution({ items }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.label} className="rounded-2xl px-4 py-3" style={{ backgroundColor: item.color }}>
          <div className="flex items-center justify-between gap-4">
            <span className="text-sm font-medium text-slate-700">{item.label}</span>
            <span className="text-sm font-bold text-slate-950">{item.value}%</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function CalificacionesPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ mensaje: "", tipo: "success" });
  function showToast(tipo, mensaje) {
    setToast({ mensaje, tipo });
  }
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [tab, setTab] = useState("resumen");

  const resumen = data?.resumen || EMPTY_ARRAY;
  const calificaciones = data?.calificaciones || EMPTY_ARRAY;
  const materias = data?.filtros?.materias || EMPTY_ARRAY;
  const promedioPorAsignatura = data?.promedio_por_asignatura || { labels: EMPTY_ARRAY, data: EMPTY_ARRAY };
  const mejoresEstudiantes = data?.mejores_estudiantes || EMPTY_ARRAY;
  const porEstudiante = data?.por_estudiante || EMPTY_ARRAY;
  const porCurso = data?.por_curso || EMPTY_ARRAY;
  const permisos = data?.permisos || { puede_crear: false, puede_ver_todo: false };
  const paginacion = data?.paginacion || { pagina: 1, paginas: 1, anterior: false, siguiente: false, total: 0 };

  const controls = useMemo(() => ({ query, page }), [query, page]);

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    const timer = window.setTimeout(() => {
      getGradesPage({ query: controls.query, page: controls.page, pageSize: 10 })
        .then((response) => {
          if (!mounted) {
            return;
          }

          setData(response);
        })
        .catch((requestError) => {
          if (!mounted) {
            return;
          }

          showToast("error", requestError?.response?.data?.error || "No fue posible cargar las calificaciones");
        })
        .finally(() => {
          if (mounted) {
            setLoading(false);
          }
        });
    }, 250);

    return () => {
      mounted = false;
      window.clearTimeout(timer);
    };
  }, [controls]);

  const handleSearchChange = (event) => {
    setQuery(event.target.value);
    setPage(1);
  };

  const summaryRanking = mejoresEstudiantes.slice(0, 5);
  const topCourseCards = porCurso.slice(0, 4);

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(59,130,246,0.08),rgba(255,255,255,0.94),rgba(14,165,233,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
            <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Calificaciones</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">Consulta las notas visibles según tu rol y las asignaciones docentes.</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700">
            {permisos.puede_ver_todo ? "Acceso total" : "Acceso limitado a tus asignaciones"}
          </div>
        </div>
      </header>

      <Toast mensaje={toast.mensaje} tipo={toast.tipo} onClose={() => setToast({ mensaje: "", tipo: "success" })} />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {resumen.map((item) => (
          <StatCard key={item.titulo} item={item} />
        ))}
      </div>

      <section className="rounded-[2rem] border border-slate-200 bg-white p-2 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <div className="flex flex-wrap gap-1 rounded-[1.5rem] bg-slate-100 p-1">
          <TabButton active={tab === "resumen"} onClick={() => setTab("resumen")}>Resumen</TabButton>
          <TabButton active={tab === "estudiante"} onClick={() => setTab("estudiante")}>Por Estudiante</TabButton>
          <TabButton active={tab === "curso"} onClick={() => setTab("curso")}>Por Curso</TabButton>
        </div>
      </section>

      {tab === "resumen" ? (
        <div className="grid gap-6 xl:grid-cols-2">
          <SectionShell title="Promedio por Asignatura" description="Vista agregada de las notas visibles">
            <div className="h-80 rounded-3xl border border-slate-100 bg-slate-50 p-4">
              <BarChartMock data={promedioPorAsignatura.data} labels={promedioPorAsignatura.labels} color="#8b5cf6" />
            </div>
          </SectionShell>

          <SectionShell title="Mejores Estudiantes" description="Ranking general del periodo visible">
            <div className="space-y-3">
              {summaryRanking.map((item) => (
                <article key={item.id} className="flex items-center justify-between rounded-3xl bg-slate-50 px-4 py-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 font-bold text-blue-700">{item.posicion}</div>
                    <div>
                      <p className="text-sm font-bold text-slate-950">{item.nombre}</p>
                      <p className="text-xs text-slate-500">ID: {item.documento}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-black text-blue-600">{item.promedio}</p>
                    <p className="text-xs text-emerald-600">{item.detalle}</p>
                  </div>
                </article>
              ))}
            </div>
          </SectionShell>
        </div>
      ) : null}

      {tab === "estudiante" ? (
        <SectionShell
          title="Calificaciones por Estudiante"
          description="Detalle de materias y promedio por alumno"
          extra={(
            <div className="flex flex-wrap items-center gap-3">
              <div className="relative">
                <svg className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <circle cx="11" cy="11" r="7" />
                  <path d="m20 20-3.5-3.5" />
                </svg>
                <input
                  value={query}
                  onChange={handleSearchChange}
                  placeholder="Buscar estudiante, curso o grado..."
                  className="w-full min-w-[280px] rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 text-sm outline-none transition focus:border-blue-300 focus:bg-white"
                />
              </div>

            </div>
          )}
        >
          <div className="overflow-hidden rounded-2xl border border-slate-200">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Estudiante</th>
                    {materias.map((materia) => (
                      <th key={materia} className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">{materia}</th>
                    ))}
                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Promedio</th>
                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Asistencia</th>
                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Tendencia</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {loading ? (
                    Array.from({ length: 5 }).map((_, index) => (
                      <tr key={index}>
                        <td className="px-4 py-4" colSpan={materias.length + 4}>
                          <div className="h-16 animate-pulse rounded-2xl bg-slate-100" />
                        </td>
                      </tr>
                    ))
                  ) : porEstudiante.length ? (
                    porEstudiante.map((item) => (
                      <tr key={item.id}>
                        <td className="px-4 py-4">
                          <p className="text-sm font-semibold text-slate-900">{item.estudiante}</p>
                          <p className="text-xs text-slate-500">ID: {item.documento}</p>
                        </td>
                        {materias.map((materia) => (
                          <td key={materia} className="px-4 py-4 text-sm font-medium text-slate-700">{item.materias[materia] ?? "-"}</td>
                        ))}
                        <td className="px-4 py-4 text-sm font-black text-blue-600">{item.promedio}</td>
                        <td className="px-4 py-4">
                          <span className={`inline-flex rounded-full px-3 py-1 text-xs font-bold ${
                            item.asistencia >= 80 ? "bg-emerald-50 text-emerald-700" :
                            item.asistencia >= 60 ? "bg-amber-50 text-amber-700" :
                            "bg-red-50 text-red-700"
                          }`}>
                            {item.asistencia}%
                          </span>
                        </td>
                        <td className="px-4 py-4"><StudentBadge value={item.tendencia} /></td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td className="px-4 py-10 text-center text-sm text-slate-500" colSpan={materias.length + 4}>
                        No se encontraron calificaciones para mostrar.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-5 flex flex-col gap-4 border-t border-slate-100 pt-5 text-sm text-slate-500 lg:flex-row lg:items-center lg:justify-between">
            <p>Mostrando {calificaciones.length} de {new Intl.NumberFormat("es-PA").format(Number(paginacion.total || 0))} calificaciones</p>
            <div className="flex items-center gap-3">
              <button type="button" disabled={!paginacion.anterior || loading} onClick={() => setPage((currentPage) => Math.max(currentPage - 1, 1))} className="rounded-2xl border border-slate-200 bg-white px-4 py-2 font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50">Anterior</button>
              <span className="rounded-2xl bg-slate-100 px-4 py-2 font-semibold text-slate-700">Página {paginacion.pagina} de {paginacion.paginas}</span>
              <button type="button" disabled={!paginacion.siguiente || loading} onClick={() => setPage((currentPage) => currentPage + 1)} className="rounded-2xl border border-slate-200 bg-white px-4 py-2 font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50">Siguiente</button>
            </div>
          </div>
        </SectionShell>
      ) : null}

      {tab === "curso" ? (
        <div className="grid gap-6 xl:grid-cols-2">
          <SectionShell title="Promedio por Curso" description="Distribución de rendimiento y promedio general">
            <div className="grid gap-4 lg:grid-cols-2">
              {topCourseCards.map((course) => (
                <article key={course.id} className="rounded-[1.75rem] border border-slate-200 bg-slate-50 p-5">
                  <h3 className="text-lg font-black text-slate-950">{course.curso}</h3>
                  <p className="mt-4 text-4xl font-black tracking-tight text-blue-600">{course.promedio}</p>
                  <p className="mt-2 text-sm text-slate-500">Promedio del curso</p>
                  <div className="mt-5 rounded-2xl border border-slate-100 bg-white p-3">
                    <CourseDistribution items={course.distribucion} />
                  </div>
                  <div className="mt-4 rounded-2xl bg-white px-4 py-3 text-sm text-slate-600">
                    <p className="font-semibold text-slate-900">{course.estudiantes} estudiantes</p>
                    <p className="mt-1">Mejor estudiante: {course.mejor_estudiante}</p>
                  </div>
                </article>
              ))}
            </div>
          </SectionShell>

          <SectionShell title="Promedio por Asignatura" description="Comparativa global visible">
            <div className="h-80 rounded-3xl border border-slate-100 bg-slate-50 p-4">
              <BarChartMock data={promedioPorAsignatura.data} labels={promedioPorAsignatura.labels} color="#8b5cf6" />
            </div>
            <div className="mt-6 rounded-3xl border border-slate-100 bg-slate-50 p-5">
              <p className="text-sm font-semibold text-slate-700">Rendimiento de Alumnos</p>
              {mejoresEstudiantes.length ? (
                <div className="mt-4 space-y-3">
                  {mejoresEstudiantes.map((item) => (
                    <div key={item.id} className="flex items-center justify-between rounded-2xl bg-white px-4 py-3 shadow-sm">
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-700">{item.posicion}</div>
                        <div>
                          <p className="text-sm font-bold text-slate-950">{item.nombre}</p>
                          <p className="text-xs text-slate-500">Prom: {item.promedio}</p>
                        </div>
                      </div>
                      <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">{item.detalle}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-2 text-sm text-slate-500">Sin datos de rendimiento disponibles.</p>
              )}
            </div>
          </SectionShell>
        </div>
      ) : null}
    </section>
  );
}

export default CalificacionesPage;