import { useEffect, useMemo, useState, useCallback } from "react";
import { createDocente, updateDocente, deleteDocente, restoreDocente, getDocentesPage } from "../../services/docentesService";
import { getStoredUser } from "../../services/authService";
import Toast from "../../components/Toast";
import Modal from "../../components/Modal";

const EMPTY_ARRAY = [];
const ROL_COLORS = {
  director: "bg-violet-100 text-violet-700",
  secretaria: "bg-blue-100 text-blue-700",
  regente: "bg-orange-100 text-orange-700",
  docente: "bg-emerald-100 text-emerald-700",
};

function DocenteCard({ docente, onUpdated, onDeleted, puedeGestionar, onToast }) {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  const nombre = docente.nombre_completo || [docente.nombre, docente.primer_apellido].filter(Boolean).join(" ") || "-";
  const inicial = nombre.charAt(0).toUpperCase();
  const rolClass = ROL_COLORS[docente.rol] || "bg-slate-100 text-slate-700";
  const d = docente.docente;

  function startEdit() {
    setForm({
      nombre: docente.nombre || "",
      apellido: docente.primer_apellido || "",
      ci: docente.ci || "",
      email: docente.email || "",
      titulo_academico: d?.titulo_academico || "",
      especialidad: d?.especialidad || "",
      fecha_ingreso_institucion: d?.fecha_ingreso_institucion || "",
      anos_experiencia: d?.anos_experiencia ?? "",
    });
    setEditing(true);
  }

  async function handleEdit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        nombre: form.nombre,
        apellido: form.primer_apellido,
        ci: form.ci,
        email: form.email,
        titulo_academico: form.titulo_academico || null,
        especialidad: form.especialidad || null,
        fecha_ingreso_institucion: form.fecha_ingreso_institucion || null,
        anos_experiencia: form.anos_experiencia !== "" ? Number(form.anos_experiencia) : null,
      };
      const updated = await updateDocente(docente.id, payload);
      onUpdated(updated);
      onToast("Docente actualizado correctamente", "success");
      setEditing(false);
    } catch (err) {
      onToast(err?.response?.data?.error || "Error al actualizar el docente", "error");
    } finally {
      setSaving(false);
    }
  }

  async function confirmToggleActive() {
    setShowConfirmModal(false);
    try {
      if (docente.activo) {
        await deleteDocente(docente.id);
        onDeleted(docente.id, { ...docente, activo: false });
        onToast("Docente deshabilitado correctamente", "success");
      } else {
        const restored = await restoreDocente(docente.id);
        onUpdated(restored);
        onToast("Docente habilitado correctamente", "success");
      }
    } catch (err) {
      onToast(err?.response?.data?.error || `Error al ${docente.activo ? "deshabilitar" : "habilitar"} el docente`, "error");
    }
  }

  return (
    <>
      <div className="rounded-2xl border border-slate-100 bg-white shadow-sm transition hover:border-slate-200 hover:shadow-md">
        {/* Main row */}
        <div className="flex items-center gap-4 px-5 py-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-slate-900 text-sm font-black text-white">
            {inicial}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-bold text-slate-950">{nombre}</p>
            <p className="truncate text-xs text-slate-500">{docente.email || "-"}</p>
          </div>
          <div className="flex shrink-0 items-center gap-3">
            {docente.ci ? <span className="hidden text-xs text-slate-400 sm:block">CI: {docente.ci}</span> : null}
            <span className={`rounded-full px-3 py-1 text-xs font-semibold ${rolClass}`}>
              {docente.rol || "docente"}
            </span>
            <span className={`h-2.5 w-2.5 rounded-full ${docente.activo ? "bg-emerald-500" : "bg-slate-300"}`} title={docente.activo ? "Activo" : "Inactivo"} />
          </div>
          {puedeGestionar ? (
            <div className="flex shrink-0 items-center gap-1">
              <button onClick={() => setExpanded(!expanded)} className="rounded-xl px-3 py-2 text-xs font-semibold text-slate-600 transition hover:bg-slate-100" title="Ver detalle">
                {expanded ? "▼" : "▶"}
              </button>
              <button onClick={startEdit} className="rounded-xl px-3 py-2 text-xs font-semibold text-blue-600 transition hover:bg-blue-50">Editar</button>
              <button onClick={() => setShowConfirmModal(true)} className={`rounded-xl px-3 py-2 text-xs font-semibold transition ${docente.activo ? "text-red-600 hover:bg-red-50" : "text-emerald-600 hover:bg-emerald-50"}`}>
                {docente.activo ? "Deshabilitar" : "Habilitar"}
              </button>
            </div>
          ) : null}
        </div>

        {/* Expandable details */}
        {expanded && !editing ? (
          <div className="border-t border-slate-100 px-5 py-4">
            <div className="grid gap-x-8 gap-y-2 text-sm sm:grid-cols-2 lg:grid-cols-3">
              <InfoRow label="CI" value={docente.ci} />
              <InfoRow label="Email" value={docente.email} />
              <InfoRow label="Rol" value={docente.rol} />
              <InfoRow label="Título académico" value={d?.titulo_academico} />
              <InfoRow label="Especialidad" value={d?.especialidad} />
              <InfoRow label="Fecha ingreso" value={d?.fecha_ingreso_institucion} />
              <InfoRow label="Años experiencia" value={d?.anos_experiencia != null ? `${d.anos_experiencia} años` : null} />
              <InfoRow label="Estado" value={docente.activo ? "Activo" : "Inactivo"} />
            </div>
          </div>
        ) : null}

        {/* Inline edit form */}
        {editing ? (
          <form onSubmit={handleEdit} className="border-t border-slate-100 px-5 py-4">
            <div className="grid gap-x-4 gap-y-3 sm:grid-cols-2 lg:grid-cols-3">
              <Field label="Nombres" name="nombre" value={form.nombre} onChange={(v) => setForm((p) => ({ ...p, nombre: v }))} />
              <Field label="Apellido Paterno" name="primer_apellido" value={form.primer_apellido} onChange={(v) => setForm((p) => ({ ...p, primer_apellido: v }))} />
              <Field label="CI" name="ci" value={form.ci} onChange={(v) => setForm((p) => ({ ...p, ci: v }))} />
              <Field label="Email" name="email" value={form.email} onChange={(v) => setForm((p) => ({ ...p, email: v }))} />
              <Field label="Título académico" name="titulo_academico" value={form.titulo_academico} onChange={(v) => setForm((p) => ({ ...p, titulo_academico: v }))} />
              <Field label="Especialidad" name="especialidad" value={form.especialidad} onChange={(v) => setForm((p) => ({ ...p, especialidad: v }))} />
              <Field label="Fecha ingreso" name="fecha_ingreso_institucion" type="date" value={form.fecha_ingreso_institucion} onChange={(v) => setForm((p) => ({ ...p, fecha_ingreso_institucion: v }))} />
              <Field label="Años experiencia" name="anos_experiencia" type="number" value={form.anos_experiencia} onChange={(v) => setForm((p) => ({ ...p, anos_experiencia: v }))} />
            </div>
            <div className="mt-4 flex gap-3">
              <button type="submit" disabled={saving} className="rounded-xl bg-slate-900 px-5 py-2 text-sm font-bold text-white transition hover:bg-slate-800 disabled:opacity-50">
                {saving ? "Guardando..." : "Guardar cambios"}
              </button>
              <button type="button" onClick={() => setEditing(false)} className="rounded-xl border border-slate-200 bg-white px-5 py-2 text-sm font-bold text-slate-700 transition hover:bg-slate-50">
                Cancelar
              </button>
            </div>
          </form>
        ) : null}
      </div>

      <Modal
        isOpen={showConfirmModal}
        mode="confirm"
        iconType={docente.activo ? "warning" : "info"}
        title={`${docente.activo ? "Deshabilitar" : "Habilitar"} docente`}
        message={`¿Está seguro que desea ${docente.activo ? "deshabilitar" : "habilitar"} a ${nombre}?`}
        confirmLabel={docente.activo ? "Deshabilitar" : "Habilitar"}
        onConfirm={confirmToggleActive}
        onCancel={() => setShowConfirmModal(false)}
      />
    </>
  );
}

function InfoRow({ label, value }) {
  return (
    <div>
      <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</span>
      <p className="mt-0.5 text-slate-700">{value || <span className="text-slate-300">—</span>}</p>
    </div>
  );
}

function Field({ label, name, value, type = "text", onChange }) {
  return (
    <label className="flex flex-col gap-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
      {label}
      <input type={type} name={name} value={value} onChange={(e) => onChange(e.target.value)} className="mt-0.5 rounded-xl border border-slate-200 px-3 py-2 text-sm font-normal normal-case text-slate-900 outline-none transition focus:border-blue-300" />
    </label>
  );
}

function DocentesPage() {
  const [usuario] = useState(getStoredUser);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ mensaje: "", tipo: "success" });
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ nombres: "", primer_apellido: "", ci: "", email: "", titulo_academico: "", especialidad: "", fecha_ingreso_institucion: "", anos_experiencia: "" });
  const [saving, setSaving] = useState(false);
  const [incluirInactivos, setIncluirInactivos] = useState(true);

  const puedeGestionar = usuario?.rol === "secretaria" || usuario?.rol === "director";
  const docentes = data?.usuarios || EMPTY_ARRAY;
  const total = data?.total || 0;
  const totalPages = data?.total_pages || 1;
  const currentPage = data?.page || 1;
  const hasPrev = currentPage > 1;
  const hasNext = currentPage < totalPages;

  const controls = useMemo(() => ({ query, page, incluirInactivos }), [query, page, incluirInactivos]);

  const fetchPage = useCallback(() => {
    setLoading(true);
    getDocentesPage({ query: controls.query, page: controls.page, pageSize: 8, incluirInactivos: controls.incluirInactivos })
      .then((r) => { setData(r); })
      .catch((err) => showToast(err?.response?.data?.error || "No fue posible cargar los docentes", "error"))
      .finally(() => setLoading(false));
  }, [controls]);

  useEffect(() => {
    const timer = window.setTimeout(fetchPage, 150);
    return () => window.clearTimeout(timer);
  }, [fetchPage]);

  function showToast(mensaje, tipo = "success") {
    setToast({ mensaje, tipo });
  }

  function handleDocenteUpdated(updated) {
    setData((prev) => {
      if (!prev) return prev;
      const list = (prev.usuarios || []).map((d) => (d.id === updated.id ? updated : d));
      return { ...prev, usuarios: list };
    });
  }

  function handleDocenteDeleted(id, updated) {
    setData((prev) => {
      if (!prev) return prev;
      const list = (prev.usuarios || []).map((d) => (d.id === id ? updated : d));
      return { ...prev, usuarios: list };
    });
    fetchPage();
  }

  async function handleCreate(e) {
    e.preventDefault();
    setSaving(true);
    try {
      const response = await createDocente(form);
      showToast(response.mensaje || "Docente creado exitosamente", "success");
      setForm({ nombres: "", primer_apellido: "", ci: "", email: "", titulo_academico: "", especialidad: "", fecha_ingreso_institucion: "", anos_experiencia: "" });
      setShowForm(false);
      setPage(1);
      fetchPage();
    } catch (err) {
      showToast(err?.response?.data?.error || "No fue posible crear el docente", "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="space-y-6">
      <Toast
        mensaje={toast.mensaje}
        tipo={toast.tipo}
        onClose={() => setToast({ mensaje: "", tipo: "success" })}
      />

      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(14,165,233,0.08),rgba(255,255,255,0.94),rgba(99,102,241,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
            <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Docentes</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">Gestiona el personal docente de la unidad educativa.</p>
          </div>
          {puedeGestionar ? (
            <button onClick={() => setShowForm(!showForm)} className="rounded-2xl bg-slate-950 px-6 py-3 text-sm font-bold text-white transition hover:bg-slate-800">
              {showForm ? "Cancelar" : "+ Nuevo docente"}
            </button>
          ) : null}
        </div>
      </header>

      {showForm ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <h2 className="text-xl font-black text-slate-950">Nuevo docente</h2>
          <p className="mt-1 text-sm text-slate-500">Completa los datos del nuevo docente.</p>
          <form onSubmit={handleCreate} className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <CreateField label="Nombres" value={form.nombres} onChange={(v) => setForm((p) => ({ ...p, nombres: v }))} required />
            <CreateField label="Apellido Paterno" value={form.primer_apellido} onChange={(v) => setForm((p) => ({ ...p, primer_apellido: v }))} required />
            <CreateField label="CI" value={form.ci} onChange={(v) => setForm((p) => ({ ...p, ci: v }))} required />
            <CreateField label="Email" value={form.email} onChange={(v) => setForm((p) => ({ ...p, email: v }))} placeholder="opcional" />
            <CreateField label="Título académico" value={form.titulo_academico} onChange={(v) => setForm((p) => ({ ...p, titulo_academico: v }))} />
            <CreateField label="Especialidad" value={form.especialidad} onChange={(v) => setForm((p) => ({ ...p, especialidad: v }))} />
            <CreateField label="Fecha ingreso" type="date" value={form.fecha_ingreso_institucion} onChange={(v) => setForm((p) => ({ ...p, fecha_ingreso_institucion: v }))} />
            <CreateField label="Años experiencia" type="number" value={form.anos_experiencia} onChange={(v) => setForm((p) => ({ ...p, anos_experiencia: v }))} />
            <div className="flex items-end gap-3 sm:col-span-2 lg:col-span-3">
              <button type="submit" disabled={saving} className="rounded-2xl bg-slate-950 px-6 py-3 text-sm font-bold text-white transition hover:bg-slate-800 disabled:opacity-50">
                {saving ? "Guardando..." : "Crear docente"}
              </button>
              <button type="button" onClick={() => { setForm({ nombres: "", primer_apellido: "", ci: "", email: "", titulo_academico: "", especialidad: "", fecha_ingreso_institucion: "", anos_experiencia: "" }); setShowForm(false); }} className="rounded-2xl border border-slate-200 bg-white px-6 py-3 text-sm font-bold text-slate-700 transition hover:bg-slate-50">
                Cancelar
              </button>
            </div>
          </form>
        </section>
      ) : null}

      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:gap-6">
            <div>
              <h2 className="text-xl font-black text-slate-950">Personal docente</h2>
              <p className="mt-1 text-sm text-slate-500">{total} docentes en total</p>
            </div>
            {puedeGestionar ? (
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={incluirInactivos}
                  onChange={(e) => { setIncluirInactivos(e.target.checked); setPage(1); }}
                  className="h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-500"
                />
                <span className="text-sm font-semibold text-slate-700">Incluir docentes inactivos</span>
              </label>
            ) : null}
          </div>
          <input
            value={query}
            onChange={(e) => { setQuery(e.target.value); setPage(1); }}
            placeholder="Buscar por nombre o email..."
            className="w-full min-w-[260px] rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white"
          />
        </div>

        <div className="mt-5 space-y-3">
          {loading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-16 animate-pulse rounded-2xl bg-slate-100" />
            ))
          ) : docentes.length ? (
            docentes.map((doc) => (
              <DocenteCard
                key={doc.id}
                docente={doc}
                onUpdated={handleDocenteUpdated}
                onDeleted={handleDocenteDeleted}
                puedeGestionar={puedeGestionar}
                onToast={showToast}
              />
            ))
          ) : (
            <div className="rounded-2xl border border-dashed border-slate-200 py-12 text-center text-sm text-slate-500">
              No se encontraron docentes.
            </div>
          )}
        </div>

        <div className="mt-5 flex flex-col gap-4 border-t border-slate-100 pt-5 text-sm text-slate-500 lg:flex-row lg:items-center lg:justify-between">
          <p>Mostrando {docentes.length} de {total} docentes</p>
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

function CreateField({ label, value, onChange, type = "text", placeholder, required }) {
  return (
    <div>
      <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}{required ? " *" : ""}</label>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} required={required} className="mt-1 w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-blue-300" />
    </div>
  );
}

export default DocentesPage;