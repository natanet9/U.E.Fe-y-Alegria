import { useEffect, useMemo, useState, useCallback } from "react";
import { getSchedulesPage, createSchedule, updateSchedule, deleteSchedule } from "../../services/schedulesService";
import { getStoredUser } from "../../services/authService";
import { getAsignacionesList } from "../../services/coursesService";
import Toast from "../../components/Toast";

const EMPTY_ARRAY = [];
const DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"];
const DIAS_MAP = { 1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes" };
function getAdminTabs(roleName) {
  const base = [
    { key: "curso", label: "Por Curso" },
    { key: "materia", label: "Por Materia" },
    { key: "profesor", label: "Por Profesor" },
  ];
  if (roleName === "director" || roleName === "secretaria" || roleName === "regente") {
    base.push({ key: "admin", label: "Administrar" });
  }
  return base;
}

const SUBJECT_COLORS = {
  "Matemáticas": "border-blue-300 bg-blue-50 text-blue-800",
  "Lenguaje": "border-emerald-300 bg-emerald-50 text-emerald-800",
  "Cs. Sociales": "border-amber-300 bg-amber-50 text-amber-800",
  "Cs. Naturales": "border-teal-300 bg-teal-50 text-teal-800",
  "Artes": "border-pink-300 bg-pink-50 text-pink-800",
  "Educación Física": "border-orange-300 bg-orange-50 text-orange-800",
  "Técnica Tecnológica": "border-violet-300 bg-violet-50 text-violet-800",
};

function getSubjectColor(area) {
  return SUBJECT_COLORS[area] || "border-slate-300 bg-slate-50 text-slate-800";
}

function HorarioCard({ horario }) {
  return (
    <div className={`rounded-xl border-2 p-3 ${getSubjectColor(horario.area)}`}>
      <p className="text-sm font-bold">{horario.area}</p>
      <p className="mt-1 text-xs text-slate-600">{horario.hora_inicio} - {horario.hora_fin}</p>
      <p className="text-xs text-slate-500">Aula: {horario.aula || "—"}</p>
      <p className="text-xs text-slate-500">{horario.docente}</p>
    </div>
  );
}

function CursoCard({ item }) {
  const horariosPorDia = {};
  DIAS.forEach((d) => { horariosPorDia[d] = []; });
  item.horarios.forEach((h) => {
    if (horariosPorDia[h.dia]) horariosPorDia[h.dia].push(h);
  });

  return (
    <article className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
      <h3 className="text-lg font-black text-slate-950">{item.curso}</h3>
      <div className="mt-4 grid grid-cols-5 gap-2">
        {DIAS.map((dia) => (
          <div key={dia}>
            <p className="mb-2 text-center text-[10px] font-bold uppercase tracking-wide text-slate-500">{dia.slice(0, 3)}</p>
            <div className="space-y-2">
              {(horariosPorDia[dia] || []).map((h) => (
                <HorarioCard key={h.id} horario={h} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </article>
  );
}

function MateriaCard({ area, horarios }) {
  const profesores = [...new Set(horarios.map((h) => h.docente))];
  return (
    <article className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
      <div className="flex items-center gap-3">
        <div className={`rounded-xl px-3 py-1 text-sm font-bold ${getSubjectColor(area)}`}>{area}</div>
        <span className="text-xs text-slate-500">{profesores.length} profesor(es)</span>
      </div>
      <div className="mt-4 space-y-2">
        {profesores.map((prof) => (
          <div key={prof} className="rounded-xl border border-slate-100 bg-slate-50 p-3">
            <p className="text-sm font-semibold text-slate-800">{prof}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {horarios.filter((h) => h.docente === prof).map((h) => (
                <span key={h.id} className="rounded-lg bg-white px-2 py-1 text-[10px] text-slate-600 shadow-sm">
                  {h.dia.slice(0, 3)} {h.hora_inicio}-{h.hora_fin} | {h.aula || "—"}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </article>
  );
}

function ProfesorCard({ docente, horarios }) {
  const areas = [...new Set(horarios.map((h) => h.area))];
  return (
    <article className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-100 text-sm font-bold text-indigo-700">
          {docente.split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase()}
        </div>
        <div>
          <h3 className="text-lg font-black text-slate-950">{docente}</h3>
          <p className="text-xs text-slate-500">{areas.join(", ")}</p>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-5 gap-2">
        {DIAS.map((dia) => (
          <div key={dia}>
            <p className="mb-2 text-center text-[10px] font-bold uppercase tracking-wide text-slate-500">{dia.slice(0, 3)}</p>
            <div className="space-y-2">
              {horarios.filter((h) => h.dia === dia).map((h) => (
                <HorarioCard key={h.id} horario={h} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </article>
  );
}

function HorariosPage() {
  const [usuario] = useState(() => getStoredUser());
  const roleRaw = usuario?.cargo || usuario?.rol || "";
  const roleName = roleRaw.toLowerCase();
  const esAdmin = roleName === "director" || roleName === "secretaria" || roleName === "regente";

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ mensaje: "", tipo: "success" });
  function showToast(tipo, mensaje) {
    setToast({ mensaje, tipo });
  }
  const [tab, setTab] = useState("curso");
  const [search, setSearch] = useState("");

  const [asignaciones, setAsignaciones] = useState([]);
  const [adminLoading, setAdminLoading] = useState(false);
  const [editId, setEditId] = useState(null);
  const [form, setForm] = useState({ docente_asignacion_id: "", dia_semana: "1", hora_inicio: "08:00", hora_fin: "09:00", aula: "" });
  const [saving, setSaving] = useState(false);

  const loadAsignaciones = useCallback(async () => {
    setAdminLoading(true);
    try {
      const res = await getAsignacionesList();
      const list = Array.isArray(res) ? res : [];
      setAsignaciones(list);
    } catch {
      setAsignaciones([]);
    } finally {
      setAdminLoading(false);
    }
  }, []);

  useEffect(() => {
    if (esAdmin) loadAsignaciones();
  }, [esAdmin, loadAsignaciones]);

  function handleFormChange(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleCreateOrUpdate() {
    if (!form.docente_asignacion_id || !form.hora_inicio || !form.hora_fin) {
      showToast("error", "Complete todos los campos requeridos");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        docente_asignacion_id: Number(form.docente_asignacion_id),
        dia_semana: Number(form.dia_semana),
        hora_inicio: form.hora_inicio,
        hora_fin: form.hora_fin,
        aula: form.aula,
      };
      if (editId) {
        await updateSchedule(editId, payload);
        showToast("success", "Horario actualizado");
      } else {
        await createSchedule(payload);
        showToast("success", "Horario creado");
      }
      setEditId(null);
      setForm({ docente_asignacion_id: "", dia_semana: "1", hora_inicio: "08:00", hora_fin: "09:00", aula: "" });
          const fresh = await getSchedulesPage({});
      setData(fresh);
    } catch (err) {
      showToast("error", err.response?.data?.error || "Error al guardar horario");
    } finally {
      setSaving(false);
    }
  }

  function handleEdit(h) {
    setEditId(h.id);
    setForm({
      docente_asignacion_id: String(h.docente_asignacion_id),
      dia_semana: String(h.dia_semana || ""),
      hora_inicio: h.hora_inicio,
      hora_fin: h.hora_fin,
      aula: h.aula || "",
    });
  }

  function handleCancelEdit() {
    setEditId(null);
    setForm({ docente_asignacion_id: "", dia_semana: "1", hora_inicio: "08:00", hora_fin: "09:00", aula: "" });
  }

  async function handleDelete(hId) {
    if (!window.confirm("¿Eliminar este horario?")) return;
    try {
      await deleteSchedule(hId);
      showToast("success", "Horario eliminado");
      const fresh = await getSchedulesPage({});
      setData(fresh);
    } catch (err) {
      showToast("error", err.response?.data?.error || "Error al eliminar horario");
    }
  }

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    getSchedulesPage({})
      .then((response) => {
        if (!mounted) return;
        setData(response);
      })
      .catch((requestError) => {
        if (!mounted) return;
        showToast("error", requestError?.response?.data?.error || "No fue posible cargar los horarios");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => { mounted = false; };
  }, []);

  const rawHorarios = useMemo(() => {
    if (!data) return EMPTY_ARRAY;
    if (Array.isArray(data)) return data;
    if (data.data && Array.isArray(data.data)) return data.data;
    return EMPTY_ARRAY;
  }, [data]);

  const flatHorarios = useMemo(() => {
    if (!rawHorarios.length) return EMPTY_ARRAY;
    const all = [];
    rawHorarios.forEach((item) => {
      item.horarios.forEach((h) => {
        all.push({ ...h, curso: item.curso });
      });
    });
    return all;
  }, [rawHorarios]);

  const filteredHorarios = useMemo(() => {
    if (!search.trim()) return rawHorarios;
    const q = search.toLowerCase();
    return rawHorarios.filter((item) => {
      const inCurso = item.curso?.toLowerCase().includes(q);
      const inArea = item.horarios?.some((h) => h.area?.toLowerCase().includes(q));
      const inDocente = item.horarios?.some((h) => h.docente?.toLowerCase().includes(q));
      return inCurso || inArea || inDocente;
    });
  }, [rawHorarios, search]);

  const porMateria = useMemo(() => {
    const map = {};
    rawHorarios.forEach((item) => {
      item.horarios.forEach((h) => {
        if (!map[h.area]) map[h.area] = [];
        map[h.area].push(h);
      });
    });
    return Object.entries(map).map(([area, horarios]) => ({ area, horarios }));
  }, [rawHorarios]);

  const filteredMaterias = useMemo(() => {
    if (!search.trim()) return porMateria;
    const q = search.toLowerCase();
    return porMateria.filter((m) =>
      m.area?.toLowerCase().includes(q) || m.horarios.some((h) => h.docente?.toLowerCase().includes(q))
    );
  }, [porMateria, search]);

  const porProfesor = useMemo(() => {
    const map = {};
    rawHorarios.forEach((item) => {
      item.horarios.forEach((h) => {
        if (!map[h.docente]) map[h.docente] = [];
        map[h.docente].push(h);
      });
    });
    return Object.entries(map).map(([docente, horarios]) => ({ docente, horarios }));
  }, [rawHorarios]);

  const filteredProfesores = useMemo(() => {
    if (!search.trim()) return porProfesor;
    const q = search.toLowerCase();
    return porProfesor.filter((p) =>
      p.docente?.toLowerCase().includes(q) || p.horarios.some((h) => h.area?.toLowerCase().includes(q))
    );
  }, [porProfesor, search]);

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(99,102,241,0.08),rgba(255,255,255,0.94),rgba(14,165,233,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
            <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Horarios</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">
              Consulta los horarios por curso, materia o profesor.
            </p>
          </div>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar curso, materia o profesor..."
            className="w-full min-w-[260px] rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-indigo-300"
          />
        </div>
      </header>

      <Toast mensaje={toast.mensaje} tipo={toast.tipo} onClose={() => setToast({ mensaje: "", tipo: "success" })} />

      <section className="rounded-[2rem] border border-slate-200 bg-white p-2 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <div className="flex flex-wrap gap-1 rounded-[1.5rem] bg-slate-100 p-1">
          {getAdminTabs(roleName).map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => setTab(t.key)}
              className={`rounded-2xl px-5 py-2 text-sm font-semibold transition ${
                tab === t.key ? "bg-white text-slate-950 shadow-sm" : "text-slate-600 hover:text-slate-950"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </section>

      {loading ? (
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-64 animate-pulse rounded-[1.75rem] border border-slate-200 bg-slate-100" />
          ))}
        </div>
      ) : tab === "curso" ? (
        filteredHorarios.length ? (
          <div className="grid gap-5 sm:grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3">
            {filteredHorarios.map((item) => (
              <CursoCard key={item.curso} item={item} />
            ))}
          </div>
        ) : (
          <div className="rounded-3xl border border-dashed border-slate-200 py-12 text-center text-sm text-slate-500">
            No se encontraron horarios.
          </div>
        )
      ) : tab === "materia" ? (
        filteredMaterias.length ? (
          <div className="grid gap-5 sm:grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3">
            {filteredMaterias.map((m) => (
              <MateriaCard key={m.area} area={m.area} horarios={m.horarios} />
            ))}
          </div>
        ) : (
          <div className="rounded-3xl border border-dashed border-slate-200 py-12 text-center text-sm text-slate-500">
            No se encontraron materias.
          </div>
        )
      ) : tab === "admin" ? (
        <div className="space-y-6">
          <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
            <h2 className="text-xl font-black text-slate-950">{editId ? "Editar Horario" : "Nuevo Horario"}</h2>
            <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-500">Docente - Curso - Área</label>
                <select
                  value={form.docente_asignacion_id}
                  onChange={(e) => handleFormChange("docente_asignacion_id", e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                >
                  <option value="">Seleccionar asignación</option>
                  {asignaciones.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.docente} — {a.curso} — {a.area} ({a.gestion})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-500">Día</label>
                <select
                  value={form.dia_semana}
                  onChange={(e) => handleFormChange("dia_semana", e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                >
                  <option value="1">Lunes</option>
                  <option value="2">Martes</option>
                  <option value="3">Miércoles</option>
                  <option value="4">Jueves</option>
                  <option value="5">Viernes</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-500">Hora Inicio</label>
                <input
                  type="time"
                  value={form.hora_inicio}
                  onChange={(e) => handleFormChange("hora_inicio", e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-500">Hora Fin</label>
                <input
                  type="time"
                  value={form.hora_fin}
                  onChange={(e) => handleFormChange("hora_fin", e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-500">Aula</label>
                <input
                  type="text"
                  value={form.aula}
                  onChange={(e) => handleFormChange("aula", e.target.value)}
                  placeholder="Ej: A-101"
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                />
              </div>
              <div className="flex items-end gap-2">
                <button
                  type="button"
                  onClick={handleCreateOrUpdate}
                  disabled={saving}
                  className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:opacity-50"
                >
                  {saving ? "Guardando..." : editId ? "Actualizar" : "Crear"}
                </button>
                {editId && (
                  <button
                    type="button"
                    onClick={handleCancelEdit}
                    className="rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-600 transition hover:bg-slate-50"
                  >
                    Cancelar
                  </button>
                )}
              </div>
            </div>
          </section>

          <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
            <h2 className="text-xl font-black text-slate-950">Horarios Registrados</h2>
            <div className="mt-6 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <th className="py-3 pr-4">Curso</th>
                    <th className="py-3 pr-4">Docente</th>
                    <th className="py-3 pr-4">Área</th>
                    <th className="py-3 pr-4">Día</th>
                    <th className="py-3 pr-4">Hora</th>
                    <th className="py-3 pr-4">Aula</th>
                    <th className="py-3 pr-4">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {flatHorarios.length ? flatHorarios.map((h) => (
                    <tr key={h.id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-3 pr-4 font-medium text-slate-900">{h.curso}</td>
                      <td className="py-3 pr-4 text-slate-600">{h.docente}</td>
                      <td className="py-3 pr-4 text-slate-600">{h.area}</td>
                      <td className="py-3 pr-4 text-slate-600">{DIAS_MAP[h.dia_semana] || h.dia}</td>
                      <td className="py-3 pr-4 text-slate-600">{h.hora_inicio} - {h.hora_fin}</td>
                      <td className="py-3 pr-4 text-slate-600">{h.aula || "—"}</td>
                      <td className="py-3 pr-4">
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() => handleEdit(h)}
                            className="rounded-lg bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-100"
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(h.id)}
                            className="rounded-lg bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-100"
                          >
                            Eliminar
                          </button>
                        </div>
                      </td>
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan={7} className="py-12 text-center text-sm text-slate-500">
                        No hay horarios registrados.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      ) : (
        filteredProfesores.length ? (
          <div className="grid gap-5 sm:grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3">
            {filteredProfesores.map((p) => (
              <ProfesorCard key={p.docente} docente={p.docente} horarios={p.horarios} />
            ))}
          </div>
        ) : (
          <div className="rounded-3xl border border-dashed border-slate-200 py-12 text-center text-sm text-slate-500">
            No se encontraron profesores.
          </div>
        )
      )}
    </section>
  );
}

export default HorariosPage;