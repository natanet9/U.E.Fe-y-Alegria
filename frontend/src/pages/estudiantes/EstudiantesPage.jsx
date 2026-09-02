import { useEffect, useMemo, useState, useRef, useCallback } from "react";
import { getStudentsPage, getStudentDetail, updateStudent, deleteStudent, restoreStudent, downloadStudentsExport } from "../../services/studentsService";
import { getStoredUser } from "../../services/authService";
import Toast from "../../components/Toast";

const EMPTY_ARRAY = [];

function formatNumber(value) {
  return new Intl.NumberFormat("es-PA").format(Number(value || 0));
}

function getStudentName(estudiante) {
  return (
    estudiante?.nombre ||
    estudiante?.nombre_completo ||
    [estudiante?.nombres, estudiante?.primer_apellido, estudiante?.segundo_apellido].filter(Boolean).join(" ") ||
    estudiante?.estudiante ||
    "Estudiante"
  );
}

function ActionsDropdown({ estudiante, usuario, onView, onEdit, onDelete, onRestore }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const rol = usuario?.rol || "";
  const activo = estudiante.estado === "activo";

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function handleAction(action) {
    setOpen(false);
    action.handler(estudiante);
  }

  const puedeEditar = rol === "secretaria";
  const acciones = [
    { label: "Ver Estudiante Completo", icon: "→", handler: onView },
  ];
  if (puedeEditar) {
    if (activo) {
      acciones.push({ label: "Editar", icon: "✎", handler: onEdit });
      acciones.push({ label: "Eliminar", icon: "✕", danger: true, handler: onDelete });
    } else {
      acciones.push({ label: "Restaurar", icon: "↩", handler: onRestore });
    }
  }

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="rounded-full px-2 py-1 hover:bg-slate-100"
        aria-label={`Acciones de ${getStudentName(estudiante)}`}
      >
        ⋮
      </button>
      {open ? (
        <div className="absolute right-0 z-50 mt-1 min-w-[180px] rounded-2xl border border-slate-200 bg-white py-2 shadow-xl">
          {acciones.map((accion) => (
            <button
              key={accion.label}
              type="button"
              onClick={() => handleAction(accion)}
              className={`flex w-full items-center gap-3 px-4 py-2 text-left text-sm transition hover:bg-slate-50 ${accion.danger ? "text-red-600" : "text-slate-700"}`}
            >
              <span className="w-4 text-center text-xs">{accion.icon}</span>
              {accion.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function StudentRow({ estudiante, usuario, onView, onEdit, onDelete, onRestore }) {
  const nombre = getStudentName(estudiante);
  const ci = estudiante.ci || "-";
  const rude = estudiante.rude || "-";
  const tienePromedio = estudiante.promedio !== undefined && estudiante.promedio !== null;
  const tieneAsistencia = estudiante.asistencia !== undefined && estudiante.asistencia !== null;
  const promedio = tienePromedio ? Number(estudiante.promedio) : null;
  const asistencia = tieneAsistencia ? Number(estudiante.asistencia) : null;
  const progressColor = asistencia >= 90 ? "bg-emerald-500" : asistencia >= 80 ? "bg-blue-500" : "bg-orange-500";

  return (
    <tr className="border-b border-slate-100 last:border-b-0">
      <td className="px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-900 text-sm font-black text-white">
            {estudiante.avatar || nombre.charAt(0).toUpperCase()}
          </div>
          <div>
            <p className="text-sm font-bold text-slate-950">{nombre}</p>
            <p className="text-xs text-slate-500">CI: {ci} | RUD: {rude}</p>
          </div>
        </div>
      </td>
      <td className="px-4 py-4">
        <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700">
          {estudiante.grado || "-"}
        </span>
      </td>
      <td className="px-4 py-4 text-sm">
        {promedio !== null ? (
          <span className="font-semibold text-blue-600">{promedio.toFixed(1)}</span>
        ) : (
          <span className="text-slate-400">-</span>
        )}
      </td>
      <td className="px-4 py-4 text-sm">
        {asistencia !== null ? (
          <div className="flex items-center gap-3">
            <div className="h-2 w-24 rounded-full bg-slate-100">
              <div className={`h-2 rounded-full ${progressColor}`} style={{ width: `${asistencia}%` }} />
            </div>
            <span>{asistencia}%</span>
          </div>
        ) : (
          <span className="text-slate-400">-</span>
        )}
      </td>
      <td className="px-4 py-4">
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${
          estudiante.estado === "activo"
            ? "bg-emerald-100 text-emerald-700"
            : "bg-red-100 text-red-700"
        }`}>
          {estudiante.estado === "activo" ? "Activo" : "Inactivo"}
        </span>
      </td>
      <td className="px-4 py-4 text-right">
        <ActionsDropdown estudiante={estudiante} usuario={usuario} onView={onView} onEdit={onEdit} onDelete={onDelete} onRestore={onRestore} />
      </td>
    </tr>
  );
}

function ModalBackdrop({ children, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-3xl bg-white p-8 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        {children}
      </div>
    </div>
  );
}

function ViewDetailModal({ estudiante, onClose }) {
  const nombre = getStudentName(estudiante);
  const fields = [
    { label: "RUDE", value: estudiante.rude },
    { label: "CI", value: estudiante.ci },
    { label: "Nombres", value: estudiante.nombres },
    { label: "Primer Apellido", value: estudiante.primer_apellido },
    { label: "Segundo Apellido", value: estudiante.segundo_apellido || "-" },
    { label: "Fecha de Nacimiento", value: estudiante.fecha_nacimiento || "-" },
    { label: "Género", value: estudiante.genero || "-" },
    { label: "País de Nacimiento", value: estudiante.pais_nacimiento || "-" },
    { label: "Discapacidad", value: estudiante.tiene_discapacidad ? "Sí" : "No" },
    ...(estudiante.tiene_discapacidad ? [{ label: "Tipo de Discapacidad", value: estudiante.tipo_discapacidad || "-" }] : []),
    { label: "TEA", value: estudiante.tiene_tea ? "Sí" : "No" },
    ...(estudiante.tiene_tea ? [{ label: "Dificultad de Aprendizaje", value: estudiante.dificultad_aprendizaje || "-" }] : []),
    { label: "Estado", value: estudiante.estado === "activo" ? "Activo" : "Inactivo" },
  ];

  return (
    <ModalBackdrop onClose={onClose}>
      <div className="flex items-center justify-between">
        <h3 className="text-2xl font-black text-slate-950">{nombre}</h3>
        <button onClick={onClose} className="rounded-full p-2 hover:bg-slate-100" aria-label="Cerrar">
          <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </button>
      </div>
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {fields.map((f) => (
          <div key={f.label}>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{f.label}</p>
            <p className="mt-1 text-sm font-medium text-slate-900">{f.value}</p>
          </div>
        ))}
      </div>
    </ModalBackdrop>
  );
}

function EditModal({ estudiante, onSave, onClose }) {
  const [form, setForm] = useState({
    rude: estudiante.rude || "",
    ci: estudiante.ci || "",
    nombres: estudiante.nombres || "",
    primer_apellido: estudiante.primer_apellido || "",
    segundo_apellido: estudiante.segundo_apellido || "",
    fecha_nacimiento: estudiante.fecha_nacimiento || "",
    genero: estudiante.genero || "",
    pais_nacimiento: estudiante.pais_nacimiento || "Bolivia",
    tiene_discapacidad: estudiante.tiene_discapacidad || false,
    tipo_discapacidad: estudiante.tipo_discapacidad || "",
    tiene_tea: estudiante.tiene_tea || false,
    dificultad_aprendizaje: estudiante.dificultad_aprendizaje || "",
  });
  const [saving, setSaving] = useState(false);

  function handleChange(e) {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({ ...prev, [name]: type === "checkbox" ? checked : value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave(estudiante.id, form);
    } finally {
      setSaving(false);
    }
  }

  return (
    <ModalBackdrop onClose={onClose}>
      <div className="flex items-center justify-between">
        <h3 className="text-2xl font-black text-slate-950">Editar Estudiante</h3>
        <button onClick={onClose} className="rounded-full p-2 hover:bg-slate-100" aria-label="Cerrar">
          <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </button>
      </div>
      <form onSubmit={handleSubmit} className="mt-6 grid gap-4 sm:grid-cols-2">
        <div>
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">RUDE</label>
          <input name="rude" value={form.rude} onChange={handleChange} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-300" />
        </div>
        <div>
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">CI</label>
          <input name="ci" value={form.ci} onChange={handleChange} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-300" />
        </div>
        <div>
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Nombres</label>
          <input name="nombres" value={form.nombres} onChange={handleChange} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-300" />
        </div>
        <div>
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Primer Apellido</label>
          <input name="primer_apellido" value={form.primer_apellido} onChange={handleChange} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-300" />
        </div>
        <div>
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Segundo Apellido</label>
          <input name="segundo_apellido" value={form.segundo_apellido} onChange={handleChange} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-300" />
        </div>
        <div>
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Fecha de Nacimiento</label>
          <input name="fecha_nacimiento" type="date" value={form.fecha_nacimiento} onChange={handleChange} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-300" />
        </div>
        <div>
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Género</label>
          <select name="genero" value={form.genero} onChange={handleChange} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-300">
            <option value="">Seleccionar</option>
            <option value="M">Masculino</option>
            <option value="F">Femenino</option>
          </select>
        </div>
        <div>
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">País de Nacimiento</label>
          <input name="pais_nacimiento" value={form.pais_nacimiento} onChange={handleChange} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-300" />
        </div>
        <div className="flex items-center gap-3">
          <input name="tiene_discapacidad" type="checkbox" checked={form.tiene_discapacidad} onChange={handleChange} className="h-4 w-4" />
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Tiene Discapacidad</label>
        </div>
        {form.tiene_discapacidad ? (
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Tipo de Discapacidad</label>
            <input name="tipo_discapacidad" value={form.tipo_discapacidad} onChange={handleChange} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-300" />
          </div>
        ) : null}
        <div className="flex items-center gap-3">
          <input name="tiene_tea" type="checkbox" checked={form.tiene_tea} onChange={handleChange} className="h-4 w-4" />
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Tiene TEA</label>
        </div>
        {form.tiene_tea ? (
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Dificultad de Aprendizaje</label>
            <input name="dificultad_aprendizaje" value={form.dificultad_aprendizaje} onChange={handleChange} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-300" />
          </div>
        ) : null}
        <div className="col-span-2 mt-4 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="rounded-2xl border border-slate-200 bg-white px-6 py-2 text-sm font-semibold text-slate-700">Cancelar</button>
          <button type="submit" disabled={saving} className="rounded-2xl bg-blue-600 px-6 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50">
            {saving ? "Guardando..." : "Guardar Cambios"}
          </button>
        </div>
      </form>
    </ModalBackdrop>
  );
}

function EstudiantesPage() {
  const [usuario] = useState(getStoredUser);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ mensaje: "", tipo: "success" });

  function showToast(tipo, mensaje) {
    setToast({ mensaje, tipo });
  }
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [incluirInactivos, setIncluirInactivos] = useState(false);
  const [modal, setModal] = useState(null);

  const estudiantes = data?.estudiantes || EMPTY_ARRAY;
  const total = data?.total || 0;
  const totalPages = data?.total_pages || 1;
  const currentPage = data?.page || 1;
  const hasPrev = currentPage > 1;
  const hasNext = currentPage < totalPages;

  const controls = useMemo(() => ({ query, page, incluirInactivos }), [query, page, incluirInactivos]);

  const fetchPage = useCallback(() => {
    setLoading(true);
    getStudentsPage({ query: controls.query, page: controls.page, pageSize: 8, incluirInactivos: controls.incluirInactivos })
      .then((response) => { setData(response); })
      .catch((err) => { showToast("error", err?.response?.data?.error || "No fue posible cargar los estudiantes"); })
      .finally(() => setLoading(false));
  }, [controls.query, controls.page, controls.incluirInactivos]);

  useEffect(() => {
    const timer = window.setTimeout(fetchPage, 250);
    return () => window.clearTimeout(timer);
  }, [fetchPage]);

  const handleSearchChange = (event) => {
    setQuery(event.target.value);
    setPage(1);
  };

  async function handleView(estudiante) {
    try {
      const detail = await getStudentDetail(estudiante.id);
      setModal({ type: "view", data: detail });
    } catch {
      showToast("error", "Error al cargar detalle del estudiante");
    }
  }

  async function handleEdit(estudiante) {
    try {
      const detail = await getStudentDetail(estudiante.id);
      setModal({ type: "edit", data: detail });
    } catch {
      showToast("error", "Error al cargar datos del estudiante");
    }
  }

  async function handleSaveEdit(id, formData) {
    try {
      await updateStudent(id, formData);
      setModal(null);
      fetchPage();
    } catch (err) {
      showToast("error", err?.response?.data?.error || "Error al guardar cambios");
    }
  }

  function handleDelete(estudiante) {
    setModal({
      type: "confirm",
      message: `¿Estás seguro de eliminar a ${getStudentName(estudiante)}?`,
      onConfirm: async () => {
        try {
          await deleteStudent(estudiante.id);
          setModal(null);
          fetchPage();
        } catch (err) {
          showToast("error", err?.response?.data?.error || "Error al eliminar");
          setModal(null);
        }
      },
    });
  }

  function handleRestore(estudiante) {
    setModal({
      type: "confirm",
      message: `¿Restaurar a ${getStudentName(estudiante)}?`,
      onConfirm: async () => {
        try {
          await restoreStudent(estudiante.id);
          setModal(null);
          fetchPage();
        } catch (err) {
          showToast("error", err?.response?.data?.error || "Error al restaurar");
          setModal(null);
        }
      },
    });
  }

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(14,165,233,0.08),rgba(255,255,255,0.94),rgba(99,102,241,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
            <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Estudiantes</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">Gestiona y monitorea a todos los estudiantes desde datos reales de la base.</p>
          </div>
        </div>
      </header>

      <Toast mensaje={toast.mensaje} tipo={toast.tipo} onClose={() => setToast({ mensaje: "", tipo: "success" })} />

      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-xl font-black text-slate-950">Lista de Estudiantes</h2>
            <p className="mt-1 text-sm text-slate-500">{total} estudiantes en total</p>
          </div>

          <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
            <div className="relative">
              <svg className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                <circle cx="11" cy="11" r="7" />
                <path d="m20 20-3.5-3.5" />
              </svg>
              <input
                value={query}
                onChange={handleSearchChange}
                placeholder="Buscar por nombre, CI o RUDE..."
                className="w-full min-w-[280px] rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 text-sm outline-none transition focus:border-blue-300 focus:bg-white"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={incluirInactivos}
                onChange={(e) => { setIncluirInactivos(e.target.checked); setPage(1); }}
                className="h-4 w-4 rounded border-slate-300"
              />
              Mostrar inactivos
            </label>
            <button
              type="button"
              onClick={() => downloadStudentsExport({ format: "xlsx", gestion: "", incluirInactivos })}
              className="rounded-2xl bg-emerald-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-emerald-700"
            >
              Exportar XLSX
            </button>
            <button
              type="button"
              onClick={() => downloadStudentsExport({ format: "csv", gestion: "", incluirInactivos })}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 hover:bg-slate-50"
            >
              Exportar CSV
            </button>
          </div>
        </div>

        <div className="mt-5 overflow-hidden rounded-2xl border border-slate-200">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Estudiante</th>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Grado</th>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Promedio</th>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Asistencia</th>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Estado</th>
                  <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wide text-slate-600">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {loading ? (
                  Array.from({ length: 4 }).map((_, index) => (
                    <tr key={index}>
                      <td className="px-4 py-4" colSpan="6">
                        <div className="h-16 animate-pulse rounded-2xl bg-slate-100" />
                      </td>
                    </tr>
                  ))
                ) : estudiantes.length ? (
                  estudiantes.map((estudiante) => (
                    <StudentRow
                      key={estudiante.id}
                      estudiante={estudiante}
                      usuario={usuario}
                      onView={handleView}
                      onEdit={handleEdit}
                      onDelete={handleDelete}
                      onRestore={handleRestore}
                    />
                  ))
                ) : (
                  <tr>
                    <td className="px-4 py-10 text-center text-sm text-slate-500" colSpan="6">
                      No se encontraron estudiantes con esos filtros.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-5 flex flex-col gap-4 border-t border-slate-100 pt-5 text-sm text-slate-500 lg:flex-row lg:items-center lg:justify-between">
          <p>Mostrando {estudiantes.length} de {formatNumber(total)} estudiantes</p>
          <div className="flex items-center gap-3">
            <button
              type="button"
              disabled={!hasPrev || loading}
              onClick={() => setPage(Math.max(currentPage - 1, 1))}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-2 font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Anterior
            </button>
            <span className="rounded-2xl bg-slate-100 px-4 py-2 font-semibold text-slate-700">
              Página {currentPage} de {totalPages}
            </span>
            <button
              type="button"
              disabled={!hasNext || loading}
              onClick={() => setPage(Math.min(currentPage + 1, totalPages))}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-2 font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Siguiente
            </button>
          </div>
        </div>
      </section>

      {modal?.type === "view" ? <ViewDetailModal estudiante={modal.data} onClose={() => setModal(null)} /> : null}
      {modal?.type === "edit" ? <EditModal estudiante={modal.data} onSave={handleSaveEdit} onClose={() => setModal(null)} /> : null}
      {modal?.type === "confirm" ? (
        <ModalBackdrop onClose={() => setModal(null)}>
          <p className="text-lg font-bold text-slate-950">{modal.message}</p>
          <div className="mt-6 flex justify-end gap-3">
            <button onClick={() => setModal(null)} className="rounded-2xl border border-slate-200 bg-white px-6 py-2 text-sm font-semibold text-slate-700">Cancelar</button>
            <button onClick={modal.onConfirm} className="rounded-2xl bg-red-600 px-6 py-2 text-sm font-semibold text-white hover:bg-red-700">Confirmar</button>
          </div>
        </ModalBackdrop>
      ) : null}
    </section>
  );
}

export default EstudiantesPage;
