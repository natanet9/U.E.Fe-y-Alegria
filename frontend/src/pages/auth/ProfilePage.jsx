import { useEffect, useState } from "react";
import { getStoredUser, changePasswordRequest } from "../../services/authService";
import apiClient from "../../services/apiClient";

export default function ProfilePage() {
  const currentUser = getStoredUser();
  const [form, setForm] = useState({ nombre: "", primer_apellido: "", segundo_apellido: "", email: "" });
  const [pass, setPass] = useState({ current: "", newPass: "", confirm: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (currentUser) {
      setForm({
        nombre: currentUser.nombre || "",
        primer_apellido: currentUser.primer_apellido || "",
        segundo_apellido: currentUser.segundo_apellido || "",
        email: currentUser.email || "",
      });
    }
  }, [currentUser]);

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSaving(true);
    try {
      const resp = await apiClient.put("/auth/me/", form);
      const usuario = resp.data.usuario;
      const stored = getStoredUser();
      if (stored) {
        Object.assign(stored, usuario);
        localStorage.setItem("auth_user", JSON.stringify(stored));
      }
      setSuccess("Perfil actualizado");
    } catch (err) {
      setError(err?.response?.data?.error || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (!pass.current || !pass.newPass) { setError("Completa todos los campos"); return; }
    if (pass.newPass !== pass.confirm) { setError("Las contraseñas no coinciden"); return; }
    setSaving(true);
    try {
      await changePasswordRequest(pass.current, pass.newPass);
      setSuccess("Contraseña actualizada");
      setPass({ current: "", newPass: "", confirm: "" });
    } catch (err) {
      setError(err?.response?.data?.error || "Error al cambiar contraseña");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(15,23,42,0.06),rgba(255,255,255,0.98),rgba(14,165,233,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">Mi cuenta</p>
        <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Perfil</h1>
        <p className="mt-2 max-w-2xl text-base text-slate-600">Edita tu información personal y cambia tu contraseña.</p>
      </header>

      {error && <div className="rounded-xl border border-red-200 bg-red-50 px-5 py-3 text-sm text-red-700">{error}</div>}
      {success && <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-5 py-3 text-sm text-emerald-700">{success}</div>}

      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <h2 className="text-xl font-black text-slate-950 mb-6">Información personal</h2>
        <form onSubmit={handleSaveProfile} className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-700">Nombre</label>
            <input value={form.nombre} onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
          </div>
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-700">Primer apellido</label>
            <input value={form.primer_apellido} onChange={(e) => setForm((f) => ({ ...f, primer_apellido: e.target.value }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
          </div>
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-700">Segundo apellido</label>
            <input value={form.segundo_apellido} onChange={(e) => setForm((f) => ({ ...f, segundo_apellido: e.target.value }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
          </div>
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-700">Email</label>
            <input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
          </div>
          <div className="sm:col-span-2">
            <button type="submit" disabled={saving} className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-50">
              {saving ? "Guardando..." : "Guardar cambios"}
            </button>
          </div>
        </form>
      </section>

      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <h2 className="text-xl font-black text-slate-950 mb-6">Cambiar contraseña</h2>
        <form onSubmit={handleChangePassword} className="grid gap-4 sm:grid-cols-3">
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-700">Contraseña actual</label>
            <input type="password" value={pass.current} onChange={(e) => setPass((p) => ({ ...p, current: e.target.value }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
          </div>
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-700">Nueva contraseña</label>
            <input type="password" value={pass.newPass} onChange={(e) => setPass((p) => ({ ...p, newPass: e.target.value }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
          </div>
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-700">Confirmar</label>
            <input type="password" value={pass.confirm} onChange={(e) => setPass((p) => ({ ...p, confirm: e.target.value }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
          </div>
          <div className="sm:col-span-3">
            <button type="submit" disabled={saving} className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-50">
              {saving ? "Actualizando..." : "Actualizar contraseña"}
            </button>
          </div>
        </form>
      </section>
    </section>
  );
}
