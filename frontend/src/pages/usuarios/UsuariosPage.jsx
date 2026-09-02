import { useEffect, useState, useCallback, useMemo } from "react";
import { listarUsuarios, crearUsuario, eliminarUsuario, restaurarUsuario } from "../../services/usuariosService";
import Toast from "../../components/Toast";
import Modal from "../../components/Modal";
import { useDialog } from "../../hooks/useDialog";
import { getStoredUser } from "../../services/authService";

const ROLES_ADMIN = [
  { value: "director", label: "Director" },
  { value: "secretaria", label: "Secretaria" },
  { value: "regente", label: "Regente" },
];
const ROLES_FILTER = [{ value: "", label: "Todos" }, ...ROLES_ADMIN];

export default function UsuariosPage() {
  const currentUser = useMemo(() => getStoredUser(), []);
  const [usuarios, setUsuarios] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [filterRol, setFilterRol] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ nombre: "", apellido: "", ci: "", email: "", rol: "secretaria", password: "123456" });
  const [toast, setToast] = useState({ mensaje: "", tipo: "success" });
  const { dialog, confirm, handleConfirm, handleCancel } = useDialog();

  const showToast = useCallback((tipo, mensaje) => setToast({ mensaje, tipo }), []);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listarUsuarios({
        roles: filterRol || undefined,
        page,
        pageSize: 10,
        incluirInactivos: true,
      });
      let lista = data.usuarios || [];
      if (!filterRol) {
        lista = lista.filter((u) => u.rol !== "docente" && u.rol !== "estudiante" && u.rol !== "tutor");
      }
      setUsuarios(lista);
      setTotal(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch {
      showToast("error", "Error al cargar usuarios");
    } finally {
      setLoading(false);
    }
  }, [filterRol, page, showToast]);

  useEffect(() => { cargar(); }, [cargar]);

  const handleCrear = async () => {
    if (!form.nombre.trim() || !form.email.trim()) {
      showToast("error", "Nombre y email son requeridos");
      return;
    }
    try {
      await crearUsuario(form);
      showToast("success", `Usuario ${form.rol} creado`);
      setShowModal(false);
      setForm({ nombre: "", apellido: "", ci: "", email: "", rol: "secretaria", password: "123456" });
      cargar();
    } catch (e) {
      showToast("error", e?.response?.data?.error || "Error al crear usuario");
    }
  };

  const puedeDesactivar = (u) => {
    if (u.id === currentUser?.id) return false;
    if (u.rol === "director") return false;
    return true;
  };

  const handleToggleActivo = async (u) => {
    if (!puedeDesactivar(u)) return;
    const ok = await confirm(
      u.activo
        ? `¿Desactivar a ${u.nombre_completo} (${u.rol})?`
        : `¿Restaurar a ${u.nombre_completo} (${u.rol})?`,
      { iconType: "warning", title: u.activo ? "Desactivar usuario" : "Restaurar usuario" }
    );
    if (!ok) return;
    try {
      if (u.activo) {
        await eliminarUsuario(u.id);
      } else {
        await restaurarUsuario(u.id);
      }
      showToast("success", u.activo ? "Usuario desactivado" : "Usuario restaurado");
      cargar();
    } catch (e) {
      showToast("error", e?.response?.data?.error || "Error al cambiar estado");
    }
  };

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(15,23,42,0.06),rgba(255,255,255,0.98),rgba(14,165,233,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">Administración</p>
            <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Usuarios del sistema</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">Gestiona directores, secretarias y regentes.</p>
          </div>
          <div className="flex items-center gap-3">
            <select value={filterRol} onChange={(e) => { setFilterRol(e.target.value); setPage(1); }} className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-300">
              {ROLES_FILTER.map((r) => (<option key={r.value} value={r.value}>{r.label}</option>))}
            </select>
            <button type="button" onClick={() => setShowModal(true)} className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800">Nuevo usuario</button>
          </div>
        </div>
      </header>

      <Toast mensaje={toast.mensaje} tipo={toast.tipo} onClose={() => setToast({ mensaje: "", tipo: "success" })} />
      <Modal
        isOpen={dialog.isOpen}
        mode={dialog.mode}
        iconType={dialog.iconType}
        title={dialog.title}
        message={dialog.message}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />

      {showModal && (
        <section className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <h2 className="text-xl font-black text-slate-950 mb-6">Nuevo usuario</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <label className="mb-2 block text-sm font-semibold text-slate-700">Nombre *</label>
              <input value={form.nombre} onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
            </div>
            <div>
              <label className="mb-2 block text-sm font-semibold text-slate-700">Apellido</label>
              <input value={form.apellido} onChange={(e) => setForm((f) => ({ ...f, apellido: e.target.value }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
            </div>
            <div>
              <label className="mb-2 block text-sm font-semibold text-slate-700">CI</label>
              <input value={form.ci} onChange={(e) => setForm((f) => ({ ...f, ci: e.target.value }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
            </div>
            <div>
              <label className="mb-2 block text-sm font-semibold text-slate-700">Email *</label>
              <input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
            </div>
            <div>
              <label className="mb-2 block text-sm font-semibold text-slate-700">Rol *</label>
              <select value={form.rol} onChange={(e) => setForm((f) => ({ ...f, rol: e.target.value }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white">
                {ROLES_ADMIN.map((r) => (<option key={r.value} value={r.value}>{r.label}</option>))}
              </select>
            </div>
            <div>
              <label className="mb-2 block text-sm font-semibold text-slate-700">Contraseña</label>
              <input value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
            </div>
          </div>
          <div className="mt-6 flex gap-3">
            <button type="button" onClick={handleCrear} className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800">Crear usuario</button>
            <button type="button" onClick={() => setShowModal(false)} className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50">Cancelar</button>
          </div>
        </section>
      )}

      <section className="overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        {loading ? (
          <div className="p-10 text-center text-sm text-slate-500">Cargando...</div>
        ) : usuarios.length === 0 ? (
          <div className="p-10 text-center text-sm text-slate-500">No hay usuarios con ese rol.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Nombre</th>
                  <th className="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Email</th>
                  <th className="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Rol</th>
                  <th className="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-600">CI</th>
                  <th className="px-5 py-4 text-center text-xs font-bold uppercase tracking-wide text-slate-600">Estado</th>
                  <th className="px-5 py-4 text-center text-xs font-bold uppercase tracking-wide text-slate-600">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {usuarios.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/80">
                    <td className="px-5 py-4">
                      <p className="text-sm font-semibold text-slate-900">{u.nombre_completo || `${u.nombre || ""} ${u.primer_apellido || ""}`}</p>
                    </td>
                    <td className="px-5 py-4 text-sm text-slate-600">{u.email}</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold text-indigo-700">{u.rol}</span>
                    </td>
                    <td className="px-5 py-4 text-sm text-slate-600">{u.ci || "—"}</td>
                    <td className="px-5 py-4 text-center">
                      <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${u.activo ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"}`}>{u.activo ? "Activo" : "Inactivo"}</span>
                    </td>
                    <td className="px-5 py-4 text-center">
                      {puedeDesactivar(u) ? (
                        <button type="button" onClick={() => handleToggleActivo(u)} className={`rounded-xl border px-4 py-2 text-xs font-semibold transition ${u.activo ? "border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100" : "border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100"}`}>
                          {u.activo ? "Desactivar" : "Restaurar"}
                        </button>
                      ) : (
                        <span className="text-xs text-slate-400">{u.rol === "director" ? "Protegido" : "Eres tú"}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-slate-200 px-5 py-4">
            <p className="text-sm text-slate-500">{total} usuarios</p>
            <div className="flex gap-2">
              <button disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))} className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50">← Anterior</button>
              <button disabled={page >= totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))} className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50">Siguiente →</button>
            </div>
          </div>
        )}
      </section>
    </section>
  );
}
