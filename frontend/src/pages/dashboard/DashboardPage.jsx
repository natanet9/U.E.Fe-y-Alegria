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
    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/70 px-5 py-6 text-sm text-slate-500">
      <p className="font-semibold text-slate-700">{title}</p>
      <p className="mt-1 leading-6">{description}</p>
    </div>
  );
}

function SectionCard({ title, badge, children, accent = "slate" }) {
  const accentStyles = {
    slate: "border-slate-200/90 bg-white",
    navy: "border-slate-200/90 bg-white border-t-4 border-t-[#0f2338]",
    amber: "border-amber-200/80 bg-white border-t-4 border-t-amber-500",
    blue: "border-slate-200/90 bg-white border-t-4 border-t-sky-600",
    emerald: "border-slate-200/90 bg-white border-t-4 border-t-emerald-600",
  };

  return (
    <section className={`rounded-3xl border p-6 shadow-sm ${accentStyles[accent] || accentStyles.slate}`}>
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight">{title}</h2>
        {badge ? (
          <span className="rounded-full bg-slate-100 border border-slate-200/80 px-3 py-1 text-xs font-semibold text-slate-600">
            {badge}
          </span>
        ) : null}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}

function StatCard({ item }) {
  const iconByTone = {
    navy: "text-[#0f2338] bg-slate-100 border border-slate-200",
    amber: "text-amber-600 bg-amber-50 border border-amber-200/80",
    emerald: "text-emerald-600 bg-emerald-50 border border-emerald-200/80",
    sky: "text-sky-700 bg-sky-50 border border-sky-200/80",
  };

  const styles = iconByTone[item.acento] || iconByTone.navy;
  const icon = {
    navy: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-6 w-6">
        <path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="10" cy="7" r="4" />
        <path d="M19 8v6" />
        <path d="M16 11h6" />
      </svg>
    ),
    sky: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-6 w-6">
        <path d="M4 4h16v16H4z" />
        <path d="M8 9h8M8 13h8" />
      </svg>
    ),
    emerald: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-6 w-6">
        <path d="M4 16l6-6 4 4 6-8" />
        <path d="M14 6h6v6" />
      </svg>
    ),
    amber: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-6 w-6">
        <path d="M20 12a8 8 0 1 1-4.5-7.2" />
        <path d="M20 4v5h-5" />
      </svg>
    ),
  };

  return (
    <article className="group rounded-3xl border border-slate-200/90 bg-white p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md hover:border-slate-300">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">{item.titulo}</h3>
          <p className="mt-3 text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900">
            {formatNumber(item.valor)}
          </p>
          <p className="mt-2 text-xs font-medium text-slate-500">{item.detalle}</p>
        </div>
        <div className={`rounded-2xl p-3 transition-transform group-hover:scale-105 ${styles}`}>
          {icon[item.acento] || icon.navy}
        </div>
      </div>
    </article>
  );
}

function DashboardPage() {
  const [usuario] = useState(() => getStoredUser());
  const roleRaw = usuario?.cargo || usuario?.rol || "";
  const roleName = roleRaw.toLowerCase();
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
      { titulo: "Total Estudiantes", valor: stats.total_estudiantes ?? 0, detalle: "Estudiantes activos", acento: "navy" },
      { titulo: "Total Docentes", valor: stats.total_docentes ?? 0, detalle: "Docentes activos", acento: "sky" },
      { titulo: "Total Asignaciones", valor: stats.total_asignaciones ?? 0, detalle: "Cursos con responsable", acento: "emerald" },
      { titulo: "Periodos Activos", valor: stats.periodos_activos ?? 0, detalle: "Periodos en curso", acento: "amber" },
    ],
    [stats],
  );

  const rendimientoSegmentos = useMemo(
    () =>
      rendimiento.length
        ? rendimiento
        : [
            { label: "Excelente", value: 0, color: "#10b981", description: "90-100 puntos" },
            { label: "Muy Bueno", value: 0, color: "#0ea5e9", description: "80-89 puntos" },
            { label: "Bueno", value: 0, color: "#f59e0b", description: "70-79 puntos" },
            { label: "Suficiente", value: 0, color: "#f97316", description: "61-69 puntos" },
            { label: "Reprobado", value: 0, color: "#ef4444", description: "Menos de 61 puntos" },
          ],
    [rendimiento],
  );

  const badgeByType = {
    warning: "bg-amber-500",
    danger: "bg-rose-500",
    ok: "bg-emerald-500",
    info: "bg-sky-500",
  };

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    import("../../services/dashboardService").then(({ getDashboardCards, getDashboardData }) => {
      getDashboardCards()
        .then((cardsPayload) => {
          if (!mounted) return;
          setDashboard((prev) => ({ ...(prev || {}), ...cardsPayload }));
        })
        .catch((err) => {
          if (!mounted) return;
          console.debug("cards load error", err?.message || err);
        })
        .finally(() => {
          if (!mounted) return;
          setLoading(false);
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
  const dashboardTitle =
    roleName === "secretaria"
      ? "Panel de Secretaría"
      : roleName === "director"
        ? "Dashboard del Director"
        : "Panel Académico";
  const dashboardDescription =
    roleName === "secretaria"
      ? "Monitoreo de asignaciones, cierres y estado general de calificaciones."
      : roleName === "docente"
        ? "Tus asignaciones, progreso de notas y estado de cierre en un solo vistazo."
        : "Resumen ejecutivo de la actividad académica. Alertas, rendimiento y asistencia en un solo vistazo.";
  const periodoActivo = dashboard?.periodo_activo;

  return (
    <section className="space-y-6 pb-8">
      {/* Banner Hero en azul marino institucional con acentos ámbar */}
      <header className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#091726] via-[#0f2338] to-[#1a3450] p-7 sm:p-9 text-white shadow-lg">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -top-24 -right-24 h-72 w-72 rounded-full bg-amber-500/15 blur-3xl"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -bottom-24 left-1/3 h-64 w-64 rounded-full bg-sky-400/10 blur-3xl"
        />

        <div className="relative z-10 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-amber-500/15 border border-amber-400/30 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-amber-300">
              <span>✦</span>
              <span>U.E. Divino Corazón de Jesús</span>
            </div>

            <h1 className="mt-3 font-serif text-3xl sm:text-4xl font-bold tracking-tight text-white">
              {greetingName ? `Bienvenido, ${greetingName}` : dashboardTitle}
            </h1>
            <p className="mt-2 max-w-2xl text-sm sm:text-base text-slate-300 leading-relaxed">
              {dashboardDescription}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 text-xs sm:text-sm">
            <span className="rounded-full bg-white/10 backdrop-blur-md border border-white/15 px-4 py-2 font-medium text-white">
              {periodoActivo ? `${periodoActivo.nombre} ${periodoActivo.gestion}` : "Periodo no definido"}
            </span>
            <span className="rounded-full bg-amber-500/20 border border-amber-400/30 px-4 py-2 font-semibold text-amber-300">
              {licenciasPendientes} licencias pendientes
            </span>
            <button
              aria-label="refresh-dashboard"
              onClick={refreshDashboard}
              className="rounded-full bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold px-4 py-2 transition shadow-sm cursor-pointer"
            >
              Refrescar
            </button>
            {lastUpdated ? (
              <span className="rounded-full bg-white/10 border border-white/15 px-3.5 py-2 text-xs text-slate-300">
                Última: {new Date(lastUpdated).toLocaleTimeString("es-PA")}
              </span>
            ) : null}
          </div>
        </div>
      </header>

      <Toast mensaje={toast.mensaje} tipo={toast.tipo} onClose={() => setToast({ mensaje: "", tipo: "success" })} />

      {/* Tarjetas KPI */}
      {!isDocente &&
        (loading ? (
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

      {/* Accesos Rápidos */}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          ...(roleName === "director" ? [{ to: "/periodos", title: "Periodos", detail: "Abrir, habilitar y enviar" }] : []),
          ...(roleName === "secretaria" ? [{ to: "/estado-notas", title: "Estado de Notas", detail: "Avance de calificaciones" }] : []),
          ...(isDocente ? [] : [{ to: "/licencias", title: "Licencias", detail: "Revisar solicitudes" }]),
          { to: "/reportes", title: "Reportes", detail: "Exportar documentos" },
        ].map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className="group rounded-3xl border border-slate-200/90 bg-white p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:border-[#0f2338]/30 hover:shadow-md"
          >
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-bold uppercase tracking-wider text-amber-600">Acceso rápido</p>
              <span className="text-slate-400 group-hover:text-[#0f2338] group-hover:translate-x-0.5 transition">→</span>
            </div>
            <h3 className="mt-2 text-lg font-bold text-slate-900">{item.title}</h3>
            <p className="mt-1 text-sm text-slate-500">{item.detail}</p>
          </Link>
        ))}
      </section>

      {isDocente && asignaciones.length > 0 && (
        <section className="rounded-3xl border border-slate-200/90 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-bold text-slate-900">Mis Asignaciones</h2>
            <span className="rounded-full bg-slate-100 border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600">
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
                    ? "bg-[#0f2338]"
                    : "bg-amber-500";
              return (
                <Link
                  key={asig.id}
                  to={`/cursos/detalle?docente_asignacion_id=${asig.id}${periodoActivo?.id ? `&periodo_id=${periodoActivo.id}` : ""}`}
                  className="rounded-2xl border border-slate-200 bg-slate-50/70 p-5 transition hover:-translate-y-0.5 hover:border-slate-300 hover:bg-white hover:shadow-md"
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
                    <p className="mt-1 text-right text-xs font-semibold text-slate-600">{asig.completitud}%</p>
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
              <div className="space-y-2.5">
                {configChecklist.items.map((item) => (
                  <div key={item.key} className="flex items-center gap-3 rounded-2xl border border-slate-100 bg-slate-50/70 px-4 py-3">
                    <div
                      className={`flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                        item.completado ? "bg-emerald-100 text-emerald-700" : "bg-slate-200/70 text-slate-500"
                      }`}
                    >
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

          <SectionCard title="Alertas" badge="Acción recomendada" accent="amber">
            <div className="space-y-3">
              {alertasCriticas.length ? (
                alertasCriticas.map((item, index) => (
                  <article key={`${item.tipo || item.mensaje}-${index}`} className="flex items-start gap-3 rounded-2xl border border-slate-100 bg-slate-50/70 px-4 py-4">
                    <div className={`mt-1.5 h-2.5 w-2.5 flex-shrink-0 rounded-full ${badgeByType[item.tipo] || badgeByType.info}`} />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-bold text-slate-900">{item.titulo || "Alerta"}</p>
                      <p className="mt-1 text-sm text-slate-600">{item.mensaje || item.detalle || item.descripcion}</p>
                    </div>
                  </article>
                ))
              ) : (
                <EmptyState title="Sin novedades críticas" description="Todos los indicadores están dentro de lo esperado." />
              )}
            </div>
          </SectionCard>

          <SectionCard title="Promedio por Asignatura" badge="Rendimiento académico" accent="navy">
            {promedioPorAsignatura.labels.length ? (
              <div className="h-80 rounded-2xl border border-slate-100 bg-slate-50/40 p-4">
                <BarChartMock data={promedioPorAsignatura.data} labels={promedioPorAsignatura.labels} color="#0f2338" />
              </div>
            ) : (
              <EmptyState title="Sin datos suficientes" description="Cuando existan notas registradas, aquí se mostrará el rendimiento por materia." />
            )}
          </SectionCard>

          <SectionCard title="Rendimiento por Curso" badge="Promedio por paralelo" accent="amber">
            {promedioPorCurso.labels.length ? (
              <div className="h-80 rounded-2xl border border-slate-100 bg-slate-50/40 p-4">
                <BarChartMock data={promedioPorCurso.data} labels={promedioPorCurso.labels} color="#f59e0b" />
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
              <div className="h-80 rounded-2xl border border-slate-100 bg-slate-50/40 p-4">
                <BarChartMock data={asistenciaPorCurso.data} labels={asistenciaPorCurso.labels} color="#0284c7" />
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
                  <article key={item.nombre} className="flex items-center justify-between rounded-2xl border border-slate-100 bg-slate-50/70 px-4 py-3">
                    <div>
                      <p className="text-sm font-bold text-slate-900">{item.nombre}</p>
                      <p className="text-xs text-slate-500">{item.mensaje}</p>
                    </div>
                    <div className="rounded-xl bg-[#0f2338] px-3 py-1 text-right">
                      <p className="text-base font-bold text-amber-400">{item.promedio}</p>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <EmptyState title="Sin destacados aún" description="El backend no devolvió estudiantes destacados para el periodo actual." />
            )}
          </SectionCard>

          <SectionCard title="Estudiantes en Riesgo" badge="Menor rendimiento" accent="amber">
            {estudiantesRiesgo.length ? (
              <div className="space-y-3">
                {estudiantesRiesgo.map((item) => (
                  <article key={item.nombre} className="flex items-center justify-between rounded-2xl border border-amber-100 bg-amber-50/40 px-4 py-3">
                    <div>
                      <p className="text-sm font-bold text-slate-900">{item.nombre}</p>
                      <p className="text-xs text-slate-500">{item.mensaje}</p>
                    </div>
                    <div className="rounded-xl bg-amber-100 px-3 py-1 text-right">
                      <p className="text-base font-bold text-amber-800">{item.promedio}</p>
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
          <SectionCard title="Docentes sin Cierre" badge="Pendientes" accent="amber">
            {docentesSinCierre.length ? (
              <div className="space-y-3">
                {docentesSinCierre.map((item) => (
                  <article key={item.id || item.docente} className="flex items-center justify-between rounded-2xl border border-slate-100 bg-slate-50/70 px-4 py-3">
                    <div>
                      <p className="text-sm font-bold text-slate-900">{item.docente}</p>
                      <p className="text-xs text-slate-500">{item.area}</p>
                    </div>
                    <div className="rounded-xl bg-amber-50 border border-amber-200 px-3 py-1 text-right">
                      <p className="text-xs font-semibold text-amber-700">Sin cerrar</p>
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