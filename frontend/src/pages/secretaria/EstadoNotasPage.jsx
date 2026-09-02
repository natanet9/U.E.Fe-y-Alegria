import { useEffect, useState, useCallback } from "react";
import { getDocenteStatus } from "../../services/gradesService";
import { listPeriodos } from "../../services/periodoService";
import { cerrarDocente, reabrirDocente } from "../../services/cierreService";
import { getStoredUser } from "../../services/authService";
import Toast from "../../components/Toast";

function ResumenCard({ titulo, valor, detalle, acento }) {
  const colors = {
    blue: "text-blue-600 bg-blue-50",
    violet: "text-violet-600 bg-violet-50",
    green: "text-emerald-600 bg-emerald-50",
    orange: "text-orange-600 bg-orange-50",
  };
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
      <h3 className="text-sm font-semibold text-slate-500">{titulo}</h3>
      <p className="mt-4 text-4xl font-black tracking-tight text-slate-950">{valor}</p>
      {detalle && <p className="mt-2 text-sm text-slate-500">{detalle}</p>}
      <div className={`mt-4 inline-flex rounded-2xl px-3 py-2 text-xs font-semibold ${colors[acento] || colors.blue}`}>
        {titulo}
      </div>
    </article>
  );
}

function DocenteRow({ item, onToggleCierre, puedeCerrar, periodoId }) {
  const barColor = item.porcentaje === 100
    ? "bg-emerald-500"
    : item.porcentaje >= 50
      ? "bg-amber-500"
      : "bg-red-500";

  return (
    <tr className="border-b border-slate-100 hover:bg-slate-50">
      <td className="py-3 px-4 text-sm font-medium text-slate-900">{item.docente}</td>
      <td className="py-3 px-4 text-sm text-slate-600">{item.curso}</td>
      <td className="py-3 px-4 text-sm text-slate-600">{item.area}</td>
      <td className="py-3 px-4 text-sm text-slate-600 text-center">{item.total_estudiantes}</td>
      <td className="py-3 px-4 text-sm text-slate-600 text-center">{item.con_notas}</td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-3">
          <div className="h-2 flex-1 rounded-full bg-slate-200">
            <div className={`h-2 rounded-full ${barColor}`} style={{ width: `${item.porcentaje}%` }} />
          </div>
          <span className={`text-xs font-bold ${item.porcentaje === 100 ? "text-emerald-600" : "text-slate-500"}`}>
            {item.porcentaje}%
          </span>
        </div>
      </td>
      <td className="py-3 px-4 text-center">
        <div className="flex items-center justify-center gap-2">
          {item.cerrado ? (
            <span className="inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
              Cerrado
            </span>
          ) : (
            <span className="inline-flex items-center rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700">
              Abierto
            </span>
          )}
          {puedeCerrar && (
            <button
              type="button"
              onClick={() => onToggleCierre(item, periodoId)}
              className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                item.cerrado
                  ? "bg-orange-50 text-orange-700 hover:bg-orange-100"
                  : "bg-blue-50 text-blue-700 hover:bg-blue-100"
              }`}
            >
              {item.cerrado ? "Reabrir" : "Cerrar"}
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}

function GradoSection({ grado, onToggleCierre, puedeCerrar, periodoId }) {
  const [open, setOpen] = useState(true);

  return (
    <section className="rounded-[2rem] border border-slate-200 bg-white shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-6 py-4 text-left"
      >
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-bold text-slate-900">{grado.grado}</h2>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
            {grado.completadas}/{grado.total_asignaciones}
          </span>
        </div>
        <svg
          className={`h-5 w-5 text-slate-400 transition ${open ? "rotate-180" : ""}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="overflow-x-auto px-6 pb-6">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-slate-200 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <th className="py-3 px-4">Docente</th>
                <th className="py-3 px-4">Curso</th>
                <th className="py-3 px-4">Área</th>
                <th className="py-3 px-4 text-center">Estud.</th>
                <th className="py-3 px-4 text-center">Con Notas</th>
                <th className="py-3 px-4 w-1/4">Avance</th>
                <th className="py-3 px-4 text-center">Cierre</th>
              </tr>
            </thead>
            <tbody>
              {grado.docentes.map((d) => (
                <DocenteRow
                  key={d.asignacion_id}
                  item={d}
                  onToggleCierre={onToggleCierre}
                  puedeCerrar={puedeCerrar}
                  periodoId={periodoId}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default function EstadoNotasPage() {
  const [data, setData] = useState(null);
  const [periodos, setPeriodos] = useState([]);
  const [periodoId, setPeriodoId] = useState("");
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);

  const usuario = getStoredUser();
  const userRole = (usuario?.cargo || usuario?.rol || "").toLowerCase();
  const puedeCerrar = userRole === "director" || userRole === "secretaria";

  const loadPeriodos = useCallback(async () => {
    try {
      const res = await listPeriodos();
      const list = Array.isArray(res) ? res : res.data || res.periodos || [];
      setPeriodos(list);
      if (list.length > 0) {
        setPeriodoId(list[0].id);
      }
    } catch {
      setToast({ mensaje: "Error al cargar periodos", tipo: "error" });
    }
  }, []);

  const loadData = useCallback(async (pid) => {
    setLoading(true);
    try {
      const result = await getDocenteStatus(pid || undefined);
      setData(result);
    } catch (err) {
      setToast({ mensaje: err.response?.data?.error || "Error al cargar estado de notas", tipo: "error" });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadPeriodos(); }, [loadPeriodos]);
  useEffect(() => { if (periodoId) loadData(periodoId); }, [periodoId, loadData]);

  const handleToggleCierre = useCallback(async (item, pid) => {
    const accion = item.cerrado ? "reabrir" : "cerrar";
    const confirmMsg = item.cerrado
      ? `¿Reabrir las notas de ${item.docente} (${item.area})?`
      : `¿Cerrar las notas de ${item.docente} (${item.area})?`;
    if (!window.confirm(confirmMsg)) return;

    try {
      if (item.cerrado) {
        await reabrirDocente(item.asignacion_id, pid);
      } else {
        await cerrarDocente(item.asignacion_id, pid);
      }
      setToast({ mensaje: `Notas ${item.cerrado ? "reabiertas" : "cerradas"} para ${item.docente}`, tipo: "success" });
      loadData(pid);
    } catch (err) {
      setToast({ mensaje: err.response?.data?.error || "Error al realizar la operación", tipo: "error" });
    }
  }, [loadData]);

  const resumen = data?.resumen || [];

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      {toast && <Toast mensaje={toast.mensaje} tipo={toast.tipo} onClose={() => setToast(null)} />}

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-slate-950">Estado de Notas por Docente</h1>
          <p className="mt-1 text-sm text-slate-500">
            Monitoreo del avance de registro de calificaciones
          </p>
        </div>
        <select
          value={periodoId}
          onChange={(e) => setPeriodoId(e.target.value)}
          className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
        >
          {periodos.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nombre} {p.gestion}
            </option>
          ))}
        </select>
      </div>

      {data?.periodo && (
        <p className="text-sm font-medium text-slate-500">
          Periodo actual: <span className="text-slate-800">{data.periodo}</span>
        </p>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600" />
        </div>
      ) : (
        <>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {resumen.map((r, i) => (
              <ResumenCard key={i} {...r} acento={["blue", "violet", "green", "orange"][i]} />
            ))}
          </div>

          {data?.grados?.length === 0 && (
            <div className="rounded-3xl border border-slate-200 bg-white p-12 text-center">
              <p className="text-lg font-medium text-slate-500">No hay asignaciones docentes activas</p>
            </div>
          )}

          <div className="space-y-6">
            {data?.grados?.map((g) => (
              <GradoSection
                key={g.grado}
                grado={g}
                onToggleCierre={handleToggleCierre}
                puedeCerrar={puedeCerrar}
                periodoId={periodoId}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}