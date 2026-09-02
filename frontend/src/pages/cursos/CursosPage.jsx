import { useEffect, useMemo, useState, useCallback, useRef } from "react";
import { createCourse, getCoursesPage, deleteCourse, restoreCourse, getCourseDetail, getCoursesDetails } from "../../services/coursesService";
import { getStoredUser } from "../../services/authService";
import Toast from "../../components/Toast";

const EMPTY_ARRAY = [];
const GESTION = new Date().getFullYear();

function CursoCard({ curso }) {
  const docentesStr = curso.docentes?.length ? curso.docentes.join(", ") : "Sin asignar";
  const areasStr = curso.areas?.length ? curso.areas.join(", ") : "";
  const gradoLabel = [curso.grado, curso.paralelo].filter(Boolean).join(" - ");

  return (
    <article className="overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white shadow-[0_18px_50px_rgba(15,23,42,0.05)] transition hover:shadow-lg">
      {/* Top accent bar */}
      <div className="h-2 bg-gradient-to-r from-blue-500 via-indigo-400 to-violet-400" />

      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <h3 className="text-lg font-black text-slate-950">{gradoLabel}</h3>
            {curso.nivel ? <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{curso.nivel}</p> : null}
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {curso.rendimiento != null ? (
              <span className={`rounded-full px-3 py-1 text-xs font-bold ${curso.rendimiento >= 60 ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
                {curso.rendimiento}
              </span>
            ) : null}
          </div>
        </div>

        {/* Teacher & area */}
        <div className="mt-3 space-y-1 text-sm">
          <p className="text-slate-600">
            <span className="font-semibold text-slate-800">Profesor:</span>{" "}
            <span className={curso.docentes?.length ? "text-slate-700" : "text-slate-400 italic"}>
              {docentesStr}
            </span>
          </p>
          {areasStr ? <p className="text-xs text-slate-500">Áreas: {areasStr}</p> : null}
        </div>

        {/* Stats grid */}
        <div className="mt-4 grid grid-cols-3 gap-3">
          <StatBox label="Estudiantes" value={curso.total_estudiantes ?? 0} icon="👤" />
          <StatBox
            label="Rendimiento"
            value={curso.rendimiento != null ? `${curso.rendimiento}` : "—"}
            accent={curso.rendimiento != null && curso.rendimiento >= 60 ? "emerald" : curso.rendimiento != null ? "red" : "slate"}
          />
          <StatBox
            label="Asistencia"
            value={curso.asistencia != null ? `${curso.asistencia}%` : "—"}
            accent={curso.asistencia != null && curso.asistencia >= 80 ? "emerald" : curso.asistencia != null ? "amber" : "slate"}
          />
        </div>

        {/* Action */}
        <div className="mt-4">
          {curso.asignacion_ids?.length > 0 ? (
            <a
              href={`/cursos/detalle?docente_asignacion_id=${curso.asignacion_ids[0]}`}
              className="block rounded-2xl bg-slate-900 px-4 py-3 text-center text-sm font-bold text-white transition hover:bg-slate-800"
            >
              Ver detalle
            </a>
          ) : (
            <p className="rounded-2xl border border-dashed border-slate-200 px-4 py-3 text-center text-xs font-semibold text-slate-400">
              Sin docente asignado
            </p>
          )}
        </div>
      </div>
    </article>
  );
}

function StatBox({ label, value, accent }) {
  const colorMap = {
    emerald: "text-emerald-600 bg-emerald-50",
    red: "text-red-600 bg-red-50",
    amber: "text-amber-600 bg-amber-50",
    slate: "text-slate-500 bg-slate-50",
  };
  const cls = colorMap[accent] || colorMap.slate;
  return (
    <div className="rounded-2xl bg-slate-50 p-3 text-center">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-1 text-lg font-black tracking-tight ${cls.split(" ")[0]}`}>
        {value}
      </p>
    </div>
  );
}

function CursosPage() {
  const [usuario] = useState(getStoredUser);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ mensaje: "", tipo: "success" });
  function showToast(tipo, mensaje) {
    setToast({ mensaje, tipo });
  }
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ usuario_id: "", curso_id: "", area_id: "", gestion: GESTION });
  const [saving, setSaving] = useState(false);

  const puedeGestionar = usuario?.rol === "secretaria" || usuario?.rol === "director";
  const cursos = data?.cursos || EMPTY_ARRAY;
  const catalogos = data?.catalogos || {};
  const total = data?.total || 0;
  const totalPages = data?.total_pages || 1;
  const currentPage = data?.page || 1;
  const hasPrev = currentPage > 1;
  const hasNext = currentPage < totalPages;

  const controls = useMemo(() => ({ query, page }), [query, page]);

  const fetchPage = useCallback(() => {
    setLoading(true);
    getCoursesPage({ query: controls.query, page: controls.page })
      .then((r) => { setData(r); })
      .catch((err) => showToast("error", err?.response?.data?.error || "No fue posible cargar los cursos"))
      .finally(() => setLoading(false));
  }, [controls]);

  // After first load, fetch per-course heavy stats once (rendimiento/asistencia)
  const detallesLoadedRef = useRef(false);
  useEffect(() => {
    if (!data || !data.cursos || !data.cursos.length) return;
    if (detallesLoadedRef.current) return;
    let mounted = true;
    const cursosVisible = data.cursos.slice(0, 12);

    const asignacionIds = [];
    cursosVisible.forEach((curso) => {
      const aid = (curso.asignacion_ids && curso.asignacion_ids[0]) || null;
      if (aid) asignacionIds.push(aid);
    });
    if (asignacionIds.length) {
      (async () => {
        try {
          const details = await getCoursesDetails({ ids: asignacionIds });
          if (!mounted) return;
          if (!details || !details.length) return;
          setData((prev) => {
            if (!prev) return prev;
            const cursos = prev.cursos.map((c) => {
              const d = details.find((it) => it && it.docente_asignacion_id && (c.asignacion_ids || []).includes(it.docente_asignacion_id));
              if (d) {
                return { ...c, rendimiento: d.rendimiento ?? null, asistencia: d.asistencia ?? null, total_estudiantes: d.total_estudiantes ?? c.total_estudiantes };
              }
              return c;
            });
            return { ...prev, cursos };
          });
        } catch (e) {
          // ignore
        } finally {
          if (mounted) detallesLoadedRef.current = true;
        }
      })();
    } else {
      detallesLoadedRef.current = true;
    }

    return () => { mounted = false; };
  }, [data]);

  useEffect(() => {
    const timer = window.setTimeout(fetchPage, 150);
    return () => window.clearTimeout(timer);
  }, [fetchPage]);



  async function handleCreate(e) {
    e.preventDefault();
    setSaving(true);
    try {
      const response = await createCourse({
        usuario_id: Number(form.usuario_id),
        curso_id: Number(form.curso_id),
        area_id: Number(form.area_id),
        gestion: Number(form.gestion),
      });
      showToast("success", response.mensaje || "Asignación creada exitosamente. Recarga la página para ver los cambios.");
      setForm({ usuario_id: "", curso_id: "", area_id: "", gestion: GESTION });
    } catch (err) {
      showToast("error", err?.response?.data?.error || "No fue posible crear la asignación");
    } finally {
      setSaving(false);
    }
  }

  const areas = catalogos.areas || EMPTY_ARRAY;
  const docentes = catalogos.docentes || EMPTY_ARRAY;
  const cursosCatalogo = catalogos.cursos || EMPTY_ARRAY;

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(99,102,241,0.08),rgba(255,255,255,0.94),rgba(14,165,233,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
            <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Cursos</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">Visión general de todos los cursos con rendimiento y asistencia.</p>
          </div>
          {puedeGestionar ? (
            <button onClick={() => setShowForm(!showForm)} className="rounded-2xl bg-slate-950 px-6 py-3 text-sm font-bold text-white transition hover:bg-slate-800">
              {showForm ? "Cancelar" : "+ Asignar docente"}
            </button>
          ) : null}
        </div>
      </header>

      <Toast mensaje={toast.mensaje} tipo={toast.tipo} onClose={() => setToast({ mensaje: "", tipo: "success" })} />

      {showForm ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <h2 className="text-xl font-black text-slate-950">Asignar docente a curso</h2>
          <p className="mt-1 text-sm text-slate-500">Selecciona un docente, curso, área y gestión.</p>
          <form onSubmit={handleCreate} className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <SelectField label="Docente" value={form.usuario_id} onChange={(v) => setForm((p) => ({ ...p, usuario_id: v }))} options={docentes} valueKey="id" labelKey="nombre_completo" placeholder="Selecciona un docente" required />
            <SelectField label="Curso" value={form.curso_id} onChange={(v) => setForm((p) => ({ ...p, curso_id: v }))} options={cursosCatalogo} valueKey="id" labelKey="grado__nombre" labelExtra="paralelo__nombre" placeholder="Selecciona un curso" required />
            <SelectField label="Área" value={form.area_id} onChange={(v) => setForm((p) => ({ ...p, area_id: v }))} options={areas} valueKey="id" labelKey="nombre" placeholder="Selecciona un área" required />
            <div>
              <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Gestión *</label>
              <input type="number" value={form.gestion} onChange={(e) => setForm((p) => ({ ...p, gestion: e.target.value }))} required className="mt-1 w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-blue-300" />
            </div>
            <div className="flex items-end gap-3 sm:col-span-2 lg:col-span-4">
              <button type="submit" disabled={saving} className="rounded-2xl bg-slate-950 px-6 py-3 text-sm font-bold text-white transition hover:bg-slate-800 disabled:opacity-50">
                {saving ? "Guardando..." : "Crear asignación"}
              </button>
              <button type="button" onClick={() => { setForm({ usuario_id: "", curso_id: "", area_id: "", gestion: GESTION }); setShowForm(false); }} className="rounded-2xl border border-slate-200 bg-white px-6 py-3 text-sm font-bold text-slate-700 transition hover:bg-slate-50">
                Cancelar
              </button>
            </div>
          </form>
        </section>
      ) : null}

      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-xl font-black text-slate-950">Todos los cursos</h2>
            <p className="mt-1 text-sm text-slate-500">{total} cursos en total</p>
          </div>
          <input
            value={query}
            onChange={(e) => { setQuery(e.target.value); setPage(1); }}
            placeholder="Buscar por grado, nivel, docente o área..."
            className="w-full min-w-[260px] rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white"
          />
        </div>

        <div className="mt-5 grid gap-5 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
          {loading ? (
            Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-64 animate-pulse rounded-[1.75rem] border border-slate-200 bg-slate-100" />
            ))
          ) : cursos.length ? (
            cursos.map((curso) => <CursoCard key={curso.id} curso={curso} />)
          ) : (
            <div className="rounded-3xl border border-dashed border-slate-200 py-12 text-center text-sm text-slate-500 sm:col-span-2 xl:col-span-3 2xl:col-span-4">
              No se encontraron cursos.
            </div>
          )}
        </div>

        <div className="mt-5 flex flex-col gap-4 border-t border-slate-100 pt-5 text-sm text-slate-500 lg:flex-row lg:items-center lg:justify-between">
          <p>Mostrando {cursos.length} de {total} cursos</p>
          <div className="flex items-center gap-3">
            <button type="button" disabled={!hasPrev || loading} onClick={() => setPage(Math.max(currentPage - 1, 1))} className="rounded-2xl border border-slate-200 bg-white px-4 py-2 font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50">
              Anterior
            </button>
            <span className="rounded-2xl bg-slate-100 px-4 py-2 font-semibold text-slate-700">Página {currentPage} de {totalPages}</span>
            <button type="button" disabled={!hasNext || loading} onClick={() => setPage(Math.min(currentPage + 1, totalPages))} className="rounded-2xl border border-slate-200 bg-white px-4 py-2 font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50">
              Siguiente
            </button>
          </div>
        </div>
      </section>
    </section>
  );
}

function SelectField({ label, value, onChange, options, valueKey, labelKey, labelExtra, placeholder, required }) {
  return (
    <div>
      <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}{required ? " *" : ""}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)} required={required} className="mt-1 w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-blue-300">
        <option value="">{placeholder || "Seleccionar..."}</option>
        {options.map((opt) => (
          <option key={opt[valueKey]} value={opt[valueKey]}>
            {opt[labelKey]}{labelExtra && opt[labelExtra] ? ` (${opt[labelExtra]})` : ""}
          </option>
        ))}
      </select>
    </div>
  );
}

export default CursosPage;