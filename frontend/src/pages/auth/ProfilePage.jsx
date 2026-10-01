import { useEffect, useState } from "react";
import { getStoredUser, changePasswordRequest, otpStatusRequest, otpSetupRequest, otpEnableRequest, otpDisableRequest } from "../../services/authService";
import apiClient from "../../services/apiClient";

export default function ProfilePage() {
  // getStoredUser() devuelve un objeto nuevo en cada render: se fija una sola vez
  // para que el useEffect de carga inicial no se dispare en bucle.
  const [currentUser] = useState(() => getStoredUser());
  const [form, setForm] = useState({ nombre: "", primer_apellido: "", segundo_apellido: "", email: "" });
  const [pass, setPass] = useState({ current: "", newPass: "", confirm: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [saving, setSaving] = useState(false);

  // ─ Verificación en dos pasos (2FA) ─
  const [otp, setOtp] = useState(null);
  const [otpMetodo, setOtpMetodo] = useState("email");
  const [otpCodigo, setOtpCodigo] = useState("");
  const [otpPassword, setOtpPassword] = useState("");
  const [otpSetup, setOtpSetup] = useState(null);
  const [otpLoading, setOtpLoading] = useState(false);
  const [otpMsg, setOtpMsg] = useState("");
  const [otpError, setOtpError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function cargarEstadoOtp() {
      try {
        const data = await otpStatusRequest();
        if (!cancelled) {
          setOtp(data);
          setOtpMetodo(data?.otp_metodo || "email");
        }
      } catch (_err) {
        // Sin sesión o endpoint no disponible: no debe romper el perfil
      }
    }

    cargarEstadoOtp();
    return () => {
      cancelled = true;
    };
  }, []);

  const iniciarOtp = async (metodo) => {
    setOtpError("");
    setOtpMsg("");
    setOtpCodigo("");
    setOtpLoading(true);
    try {
      const data = await otpSetupRequest(metodo);
      setOtpSetup(data);
      setOtpMetodo(data?.metodo || metodo);
      setOtpMsg(data?.mensaje || "Confirma la activación con el código recibido.");
    } catch (err) {
      setOtpError(err?.response?.data?.error || "No se pudo iniciar la configuración");
    } finally {
      setOtpLoading(false);
    }
  };

  const confirmarOtp = async (e) => {
    e.preventDefault();
    setOtpError("");
    setOtpMsg("");
    setOtpLoading(true);
    try {
      const data = await otpEnableRequest(otpCodigo);
      setOtp(data);
      setOtpSetup(null);
      setOtpCodigo("");
      setOtpMsg("Verificación en dos pasos activada");
    } catch (err) {
      setOtpError(err?.response?.data?.error || "Código incorrecto");
    } finally {
      setOtpLoading(false);
    }
  };

  const desactivarOtp = async (e) => {
    e.preventDefault();
    setOtpError("");
    setOtpMsg("");
    setOtpLoading(true);
    try {
      const data = await otpDisableRequest({ password: otpPassword });
      setOtp(data);
      setOtpPassword("");
      setOtpMsg("Verificación en dos pasos desactivada");
    } catch (err) {
      setOtpError(err?.response?.data?.error || "No se pudo desactivar");
    } finally {
      setOtpLoading(false);
    }
  };

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

      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <h2 className="text-xl font-black text-slate-950">Verificación en dos pasos</h2>
        <p className="mt-2 text-sm text-slate-600">
          Además de tu contraseña, el sistema pedirá un código de 6 dígitos al iniciar sesión.
        </p>

        {otpError && <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-5 py-3 text-sm text-red-700">{otpError}</div>}
        {otpMsg && <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-5 py-3 text-sm text-emerald-700">{otpMsg}</div>}

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${otp?.otp_habilitado ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-600"}`}>
            {otp?.otp_habilitado ? `Activado (${otp?.otp_metodo || "totp"})` : "Desactivado"}
          </span>
          {otp?.otp_habilitado ? (
            <span className="text-xs text-slate-500">Usa los códigos de 6 dígitos de tu aplicación Google Authenticator</span>
          ) : null}
        </div>

        {otp?.otp_habilitado ? (
          <form onSubmit={desactivarOtp} className="mt-5 flex flex-wrap items-end gap-3">
            <div>
              <label className="mb-2 block text-sm font-semibold text-slate-700" htmlFor="otp-password">Contraseña actual</label>
              <input
                id="otp-password"
                type="password"
                value={otpPassword}
                onChange={(e) => setOtpPassword(e.target.value)}
                className="w-64 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white"
                placeholder="Confirma para desactivar"
              />
            </div>
            <button
              type="submit"
              disabled={otpLoading || !otpPassword}
              className="rounded-2xl border border-rose-200 bg-rose-50 px-5 py-3 text-sm font-semibold text-rose-700 transition hover:bg-rose-100 disabled:opacity-50"
            >
              {otpLoading ? "Procesando..." : "Desactivar"}
            </button>
          </form>
        ) : (
          <div className="mt-5 flex flex-col gap-4">
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => iniciarOtp("totp")}
                disabled={otpLoading}
                className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-50"
              >
                Configurar con Google Authenticator
              </button>
            </div>

            {otpSetup?.metodo === "totp" && (otpSetup?.qr_code || otpSetup?.secreto) ? (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6 space-y-4">
                <div className="text-center">
                  <h3 className="text-base font-bold text-slate-900 m-0">1. Escanea el código QR</h3>
                  <p className="text-xs text-slate-500 mt-1 m-0">
                    Abre <b>Google Authenticator</b> o <b>Microsoft Authenticator</b> en tu celular y escanea este código:
                  </p>
                </div>

                {otpSetup.qr_code && (
                  <div className="flex justify-center my-2">
                    <div className="bg-white p-3 rounded-2xl shadow-sm border border-slate-200 inline-block">
                      <img
                        src={otpSetup.qr_code}
                        alt="Código QR de autenticación"
                        className="w-52 h-52 object-contain"
                      />
                    </div>
                  </div>
                )}

                <div className="rounded-xl border border-slate-200 bg-white p-3 text-xs space-y-1">
                  <span className="font-semibold text-slate-700 block">¿No puedes escanear el QR? Ingresa la clave manualmente:</span>
                  <span className="font-mono text-sm text-slate-950 font-bold select-all block bg-slate-50 px-3 py-2 rounded border border-slate-100 break-all">
                    {otpSetup.secreto}
                  </span>
                  <span className="text-slate-400 block text-[11px]">Cuenta: {otpSetup.cuenta || "U.E. Fe y Alegría"}</span>
                </div>
              </div>
            ) : null}

            {otpSetup ? (
              <form onSubmit={confirmarOtp} className="flex flex-col sm:flex-row sm:items-end gap-3 pt-2">
                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-700" htmlFor="otp-codigo">
                    Código de 6 dígitos
                  </label>
                  <input
                    id="otp-codigo"
                    value={otpCodigo}
                    onChange={(e) => setOtpCodigo(e.target.value.replace(/\D/g, ""))}
                    inputMode="numeric"
                    maxLength={6}
                    className="w-44 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-center text-lg tracking-[0.4em] outline-none transition focus:border-blue-300 focus:bg-white"
                    placeholder="000000"
                  />
                </div>
                <button
                  type="submit"
                  disabled={otpLoading || otpCodigo.length !== 6}
                  className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-50"
                >
                  {otpLoading ? "Verificando..." : "Confirmar activación"}
                </button>
              </form>
            ) : (
              <p className="m-0 text-xs text-slate-500">
                Método recomendado: aplicación autenticadora (Google Authenticator / Microsoft Authenticator).
              </p>
            )}
          </div>
        )}
      </section>
    </section>
  );
}
