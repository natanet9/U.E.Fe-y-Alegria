import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getStoredUser } from "../../services/authService";
import { getDashboardData, clearDashboardCache } from "../../services/dashboardService";
import BarChartMock from "../../components/charts/BarChartMock";
import PieChartMock from "../../components/charts/PieChartMock";
import Toast from "../../components/Toast";

const EMPTY_ARRAY = [];
const EMPTY_STATS = {
  total_estudiantes: 0,
  total_docentes: 0,
  total_asignaciones: 0,
  periodos_activos: 0,
};

function formatNumber(value) {
  return new Intl.NumberFormat("es-PA").format(Number(value || 0));
}

function EmptyState({ title, description }) {
  return (
    <div className="rounded-3xl border border-dashed border-slate-200 bg-slate-50 px-5 py-6 text-sm text-slate-500">
      <p className="font-semibold text-slate-700">{title}</p>
      <p className="mt-1 leading-6">{description}</p>
    </div>
  );
}

function SectionCard({ title, badge, children, accent = "slate" }) {
  const accentStyles = {
    slate: "border-slate-200 bg-white",
    blue: "border-blue-200 bg-blue-50/40",
    violet: "border-violet-200 bg-violet-50/40",
    orange: "border-orange-200 bg-orange-50/50",
    emerald: "border-emerald-200 bg-emerald-50/40",
  };

  return (
    <section className={`rounded-[2rem] border p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)] ${accentStyles[accent] || accentStyles.slate}`}>
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-xl font-black text-slate-950">{title}</h2>
        {badge ? <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-500 shadow-sm">{badge}</span> : null}
      </div>
      <div className="mt-6">{children}</div>
    </section>
  );
}

function StatCard({ item }) {
  const iconByTone = {
    blue: "text-blue-600 bg-blue-50",
    violet: "text-violet-600 bg-violet-50",
    green: "text-emerald-600 bg-emerald-50",
    orange: "text-orange-600 bg-orange-50",
  };

  const styles = iconByTone[item.acento] || iconByTone.blue;
  const icon = {
    blue: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-6 w-6">
        <path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="10" cy="7" r="4" />
        <path d="M19 8v6" />
        <path d="M16 11h6" />
      </svg>
    ),
    violet: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-6 w-6">
        <path d="M4 4h16v16H4z" />
        <path d="M8 9h8M8 13h8" />
      </svg>
    ),
    green: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-6 w-6">
        <path d="M4 16l6-6 4 4 6-8" />
        <path d="M14 6h6v6" />
      </svg>
    ),
    orange: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-6 w-6">
        <path d="M20 12a8 8 0 1 1-4.5-7.2" />
        <path d="M20 4v5h-5" />
      </svg>
    ),
  };

  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-600">{item.titulo}</h3>
          <p className="mt-5 text-4xl font-black tracking-tight text-slate-950">{formatNumber(item.valor)}</p>
          <p className="mt-2 text-sm text-slate-500">{item.detalle}</p>
        </div>
        <div className={`rounded-2xl p-3 ${styles}`}>{icon[item.acento] || icon.blue}</div>
      </div>
    </article>
  );
}

function DashboardPage() {
  const [usuario] = useState(() => getStoredUser());
  const roleRaw = usuario?.cargo || usuario?.rol || "";
  const roleName = roleRaw.toLowerCase();
  const isAdmin = roleName === "director" || roleName === "secretaria";
  const isDocente = roleName === "docente";
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [heavyLoading, setHeavyLoading] = useState(true);
  const [toast, setToast] = useState({ mensaje: "", tipo: "success" });
  function showToast(tipo, mensaje) {
    setToast({ mensaje, tipo });
  }

  const stats = dashboard?.stats || EMPTY_STATS;
  const alertasCriticas = dashboard?.alertas || [];
  const licenciasPendientes = Number(dashboard?.licencias_pendientes || 0);
  const promedioPorAsignatura = dashboard?.promedio_por_asignatura || { labels: EMPTY_ARRAY, data: EMPTY_ARRAY };
  const promedioPorCurso = dashboard?.promedio_por_curso || { labels: EMPTY_ARRAY, data: EMPTY_ARRAY };
  const asistenciaPorCurso = dashboard?.asistencia_por_curso || { labels: EMPTY_ARRAY, data: EMPTY_ARRAY };
  const rendimiento = dashboard?.rendimiento || EMPTY_ARRAY;
  const estudiantesDestacados = dashboard?.estudiantes_destacados || EMPTY_ARRAY;
  const estudiantesRiesgo = dashboard?.estudiantes_riesgo || EMPTY_ARRAY;
  const estudiantesConNotas = dashboard?.estudiantes_con_notas || 0;
  const configChecklist = dashboard?.config_checklist || { items: [], completados: 0, total: 0 };
  const docentesSinCierre = dashboard?.docentes_sin_cierre || EMPTY_ARRAY;
  const asignaciones = dashboard?.asignaciones || EMPTY_ARRAY;

  const indicadores = useMemo(
    () => [
      { titulo: "Total Estudiantes", valor: stats.total_estudiantes ?? 0, detalle: "Estudiantes activos", acento: "blue" },
      { titulo: "Total Docentes", valor: stats.total_docentes ?? 0, detalle: "Docentes activos", acento: "violet" },
      { titulo: "Total Asignaciones", valor: stats.total_asignaciones ?? 0, detalle: "Cursos con responsable", acento: "green" },
      { titulo: "Periodos Activos", valor: stats.periodos_activos ?? 0, detalle: "Periodos en curso", acento: "orange" },
    ],
    [stats],
  );

  const rendimientoSegmentos = useMemo(
    () => rendimiento.length
      ? rendimiento
      : [
        { label: "Excelente", value: 0, color: "#10b981", description: "90-100 puntos" },
        { label: "Muy Bueno", value: 0, color: "#3b82f6", description: "80-89 puntos" },
        { label: "Bueno", value: 0, color: "#f59e0b", description: "70-79 puntos" },
        { label: "Suficiente", value: 0, color: "#f97316", description: "61-69 puntos" },
        { label: "Reprobado", value: 0, color: "#ef4444", description: "Menos de 61 puntos" },
      ],
    [rendimiento],
  );

  const badgeByType = {
    warning: "bg-orange-500",
    danger: "bg-red-500",
    ok: "bg-emerald-500",
    info: "bg-blue-500",
  };

  useEffect(() => {
    let mounted = true;

    // First, fetch the lightweight cards payload so the user sees KPIs fast.
    setLoading(true);
    // Use the cards-specific fast endpoint/cache
    import("../../services/dashboardService").then(({ getDashboardCards, getDashboardData }) => {
      getDashboardCards()
        .then((cardsPayload) => {
          if (!mounted) return;
          setDashboard((prev) => ({ ...(prev || {}), ...cardsPayload }));
        })
        .catch((err) => {
          if (!mounted) return;
          // ignore cards error; show full error below when heavy load fails
          console.debug("cards load error", err?.message || err);
        })
        .finally(() => {
          if (!mounted) return;
          setLoading(false);
          // Start loading heavy data in background
          setHeavyLoading(true);
          getDashboardData()
            .then((full) => {
              if (!mounted) return;
              setDashboard(full);
            })
            .catch((requestError) => {
              if (!mounted) return;
              showToast("error", requestError?.response?.data?.error || "No fue posible cargar el dashboard");
            })
            .finally(() => {
              if (!mounted) return;
              setHeavyLoading(false);
            });
        });
    });

    return () => {
      mounted = false;
    };
  }, []);

  const [lastUpdated, setLastUpdated] = useState(null);

  async function refreshDashboard() {
    setLoading(true);
    try {
      clearDashboardCache();
      const data = await getDashboardData({ force: true });
      setDashboard(data);
      setLastUpdated(new Date());
    } catch (err) {
      showToast("error", err?.response?.data?.error || "No fue posible refrescar el dashboard");
    } finally {
      setLoading(false);
    }
  }

  const greetingName = usuario?.nombre_completo || usuario?.nombre || "";
  const dashboardTitle = roleName === "secretaria"
    ? "Panel de Secretaría"
    : roleName === "director"
      ? "Dashboard del Director"
      : "Panel Académico";
  const dashboardDescription = roleName === "secretaria"
    ? "Monitoreo de asignaciones, cierres y estado general de calificaciones."
    : roleName === "docente"
      ? "Tus asignaciones, progreso de notas y estado de cierre en un solo vistazo."
      : "Resumen ejecutivo de la actividad académica. Alertas, rendimiento y asistencia en un solo vistazo.";
  const periodoActivo = dashboard?.periodo_activo;

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(15,23,42,0.06),rgba(255,255,255,0.97),rgba(37,99,235,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E. Panama</p>
            <h1 className="mt-3 text-4xl font-black tracking-tight text-slate-950">
              {greetingName ? `Bienvenido, ${greetingName}` : dashboardTitle}
            </h1>
            <p className="mt-2 max-w-3xl text-base text-slate-600">
              {dashboardDescription}
            </p>
          </div>
          <div className="flex flex-wrap gap-3 text-sm text-slate-500">
            <span className="rounded-full border border-slate-200 bg-white px-4 py-2">
              {periodoActivo ? `${periodoActivo.nombre} ${periodoActivo.gestion}` : "Periodo no definido"}
            </span>
            <span className="rounded-full border border-slate-200 bg-white px-4 py-2">{licenciasPendientes} licencias pendientes</span>
            <button
              aria-label="refresh-dashboard"
              onClick={refreshDashboard}
              className="ml-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm hover:bg-slate-50"
            >
              Refrescar
            </button>
            {lastUpdated ? (
              <span className="rounded-full border border-slate-200 bg-white px-4 py-2">Última: {new Date(lastUpdated).toLocaleTimeString('es-PA')}</span>
            ) : null}
          </div>
        </div>
      </header>

      <Toast mensaje={toast.mensaje} tipo={toast.tipo} onClose={() => setToast({ mensaje: "", tipo: "success" })} />

      {!isDocente && (loading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-36 animate-pulse rounded-3xl border border-slate-200 bg-white" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {indicadores.map((item) => (
            <StatCard key={item.titulo} item={item} />
          ))}
        </div>
      ))}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          ...(roleName === "director" ? [{ to: "/periodos", title: "Periodos", detail: "Abrir, habilitar y enviar" }] : []),
          ...(roleName === "secretaria" ? [{ to: "/estado-notas", title: "Estado de Notas", detail: "Avance de calificaciones" }] : []),
          ...(isDocente ? [] : [{ to: "/licencias", title: "Licencias", detail: "Revisar solicitudes" }]),
          { to: "/reportes", title: "Reportes", detail: "Exportar documentos" },
        ].map((item) => (
          <Link key={item.to} to={item.to} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_18px_50px_rgba(15,23,42,0.05)] transition hover:-translate-y-0.5 hover:border-slate-300">
            <p className="text-sm font-semibold text-slate-500">Acceso rápido</p>
            <h3 className="mt-2 text-lg font-black text-slate-950">{item.title}</h3>
            <p className="mt-1 text-sm text-slate-600">{item.detail}</p>
          </Link>
        ))}
      </section>

      {isDocente && asignaciones.length > 0 && (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-black text-slate-950">Mis Asignaciones</h2>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">
              {periodoActivo ? `${periodoActivo.nombre} ${periodoActivo.gestion}` : "Sin periodo activo"}
            </span>
          </div>
          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {asignaciones.map((asig) => {
              const progressColor = asig.cerrado
                ? "bg-slate-300"
                : asig.completitud >= 100
                  ? "bg-emerald-500"
                  : asig.completitud >= 50
                    ? "bg-blue-500"
                    : "bg-amber-500";
              return (
                <Link
                  key={asig.id}
                  to={`/cursos/detalle?docente_asignacion_id=${asig.id}${periodoActivo?.id ? `&periodo_id=${periodoActivo.id}` : ""}`}
                  className="rounded-2xl border border-slate-200 bg-slate-50 p-5 transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-bold text-slate-900">{asig.curso}</p>
                      <p className="mt-0.5 text-sm text-slate-500">{asig.area}</p>
                    </div>
                    {asig.cerrado ? (
                      <span className="shrink-0 rounded-full bg-slate-200 px-3 py-1 text-xs font-semibold text-slate-600">Cerrado</span>
                    ) : (
                      <span className="shrink-0 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">Abierto</span>
                    )}
                  </div>
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span>{asig.estudiantes_con_notas || 0}/{asig.total_estudiantes || 0} estudiantes</span>
                      <span>{asig.actividades_count || 0} actividades</span>
                    </div>
                    <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-200">
                      <div
                        className={`h-full rounded-full transition-all ${progressColor}`}
                        style={{ width: `${Math.min(asig.completitud, 100)}%` }}
                      />
                    </div>
                    <p className="mt-1 text-right text-xs font-semibold text-slate-500">{asig.completitud}%</p>
                  </div>
                </Link>
              );
            })}
          </div>
        </section>
      )}

      {roleName === "director" && (
        <div className="grid gap-6 xl:grid-cols-2">
          <SectionCard title="Configuración del Sistema" badge={`${configChecklist.completados}/${configChecklist.total}`} accent="emerald">
            {configChecklist.items.length ? (
              <div className="space-y-2">
                {configChecklist.items.map((item) => (
                  <div key={item.key} className="flex items-center gap-3 rounded-2xl bg-white px-4 py-3 shadow-sm">
                    <div className={`flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                      item.completado ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-400"
                    }`}>
                      {item.completado ? "✓" : "·"}
                    </div>
                    <span className={`text-sm ${item.completado ? "text-slate-600" : "font-semibold text-slate-900"}`}>
                      {item.label}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="Sin información de configuración" description="No se pudo obtener el estado de la configuración del sistema." />
            )}
          </SectionCard>

          <SectionCard title="Alertas" badge="Acción recomendada" accent="orange">
            <div className="space-y-3">
              {alertasCriticas.length ? (
                alertasCriticas.map((item, index) => (
                  <article key={`${item.tipo || item.mensaje}-${index}`} className="flex items-start gap-3 rounded-2xl bg-white px-4 py-4 shadow-sm">
                    <div className={`mt-1 h-3 w-3 rounded-full ${badgeByType[item.tipo] || badgeByType.info}`} />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-bold text-slate-950">{item.titulo || "Alerta"}</p>
                      <p className="mt-1 text-sm text-slate-600">{item.mensaje || item.detalle || item.descripcion}</p>
                    </div>
                  </article>
                ))
              ) : (
                <EmptyState title="Sin novedades críticas" description="Todos los indicadores están dentro de lo esperado." />
              )}
            </div>
          </SectionCard>

          <SectionCard title="Promedio por Asignatura" badge="Rendimiento académico" accent="violet">
            {promedioPorAsignatura.labels.length ? (
              <div className="h-80 rounded-3xl border border-slate-100 bg-white p-4">
                <BarChartMock data={promedioPorAsignatura.data} labels={promedioPorAsignatura.labels} color="#8b5cf6" />
              </div>
            ) : (
              <EmptyState title="Sin datos suficientes" description="Cuando existan notas registradas, aquí se mostrará el rendimiento por materia." />
            )}
          </SectionCard>

          <SectionCard title="Rendimiento por Curso" badge="Promedio por paralelo" accent="orange">
            {promedioPorCurso.labels.length ? (
              <div className="h-80 rounded-3xl border border-slate-100 bg-white p-4">
                <BarChartMock data={promedioPorCurso.data} labels={promedioPorCurso.labels} color="#f97316" />
              </div>
            ) : (
              <EmptyState title="Sin datos suficientes" description="Cuando existan notas registradas, aquí se mostrará el rendimiento por curso." />
            )}
          </SectionCard>
        </div>
      )}

      {roleName === "director" && (
        <div className="grid gap-6 xl:grid-cols-2">
          <SectionCard title="Asistencia por Curso" badge="Últimos 7 días" accent="blue">
            {asistenciaPorCurso.labels.length ? (
              <div className="h-80 rounded-3xl border border-slate-100 bg-white p-4">
                <BarChartMock data={asistenciaPorCurso.data} labels={asistenciaPorCurso.labels} color="#3b82f6" />
              </div>
            ) : (
              <EmptyState title="Sin datos de asistencia" description="No hay registros de asistencia para los últimos 7 días." />
            )}
          </SectionCard>

          <SectionCard title="Distribución de Rendimiento" badge="Panorama general" accent="emerald">
            {rendimientoSegmentos.some((segmento) => Number(segmento.value || 0) > 0) ? (
              <PieChartMock segments={rendimientoSegmentos} title="Rendimiento" totalStudents={estudiantesConNotas} />
            ) : (
              <EmptyState title="Sin distribución" description="No hay suficientes notas para mostrar la distribución de rendimiento." />
            )}
          </SectionCard>
        </div>
      )}

      {roleName === "director" && (
        <div className="grid gap-6 xl:grid-cols-2">
          <SectionCard title="Estudiantes Destacados" badge="Mejores promedios" accent="blue">
            {estudiantesDestacados.length ? (
              <div className="space-y-3">
                {estudiantesDestacados.map((item) => (
                  <article key={item.nombre} className="flex items-center justify-between rounded-2xl border border-blue-100 bg-white px-4 py-3 shadow-sm">
                    <div>
                      <p className="text-sm font-bold text-slate-950">{item.nombre}</p>
                      <p className="text-xs text-slate-500">{item.mensaje}</p>
                    </div>
                    <div className="rounded-xl bg-blue-50 px-3 py-1 text-right">
                      <p className="text-lg font-black text-blue-700">{item.promedio}</p>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <EmptyState title="Sin destacados aún" description="El backend no devolvió estudiantes destacados para el periodo actual." />
            )}
          </SectionCard>

          <SectionCard title="Estudiantes en Riesgo" badge="Menor rendimiento" accent="orange">
            {estudiantesRiesgo.length ? (
              <div className="space-y-3">
                {estudiantesRiesgo.map((item) => (
                  <article key={item.nombre} className="flex items-center justify-between rounded-2xl border border-orange-100 bg-white px-4 py-3 shadow-sm">
                    <div>
                      <p className="text-sm font-bold text-slate-950">{item.nombre}</p>
                      <p className="text-xs text-slate-500">{item.mensaje}</p>
                    </div>
                    <div className="rounded-xl bg-red-50 px-3 py-1 text-right">
                      <p className="text-lg font-black text-red-600">{item.promedio}</p>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <EmptyState title="Sin estudiantes en riesgo" description="Todos los estudiantes están por encima del mínimo de aprobación (51 pts)." />
            )}
          </SectionCard>
        </div>
      )}

      {!isDocente && (
        <div className="grid gap-6 xl:grid-cols-2">
          <SectionCard title="Docentes sin Cierre" badge="Pendientes" accent="orange">
          {docentesSinCierre.length ? (
            <div className="space-y-3">
              {docentesSinCierre.map((item) => (
                <article key={item.id || item.docente} className="flex items-center justify-between rounded-2xl border border-orange-100 bg-white px-4 py-3 shadow-sm">
                  <div>
                    <p className="text-sm font-bold text-slate-950">{item.docente}</p>
                    <p className="text-xs text-slate-500">{item.area}</p>
                  </div>
                  <div className="rounded-xl bg-orange-50 px-3 py-1 text-right">
                    <p className="text-xs font-semibold text-orange-600">Sin cerrar</p>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <EmptyState title="Todos los docentes cerraron" description="No hay docentes pendientes de cierre en el periodo activo." />
          )}
        </SectionCard>
      </div>
      )}
    </section>
  );
}

export default DashboardPage;
