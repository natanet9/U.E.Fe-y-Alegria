import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { usePadres } from "../../context/PadresContext";
import { logoutRequest, changePasswordRequest } from "../../services/authService";

export default function PadresPerfilPage() {
  const navigate = useNavigate();
  const { usuario, setUsuario, pwaInstallable, promptInstallPwa, estudiantes } = usePadres();

  const [cambiandoPass, setCambiandoPass] = useState(false);
  const [actualPass, setActualPass] = useState("");
  const [nuevaPass, setNuevaPass] = useState("");
  const [confirmarPass, setConfirmarPass] = useState("");
  const [passError, setPassError] = useState("");
  const [passSuccess, setPassSuccess] = useState("");
  const [guardandoPass, setGuardandoPass] = useState(false);
  const [cerrandoSesion, setCerrandoSesion] = useState(false);

  const handleLogout = async () => {
    if (cerrandoSesion) return;
    setCerrandoSesion(true);
    try {
      await logoutRequest();
      setUsuario?.(null);
    } finally {
      navigate("/padres/login", { replace: true });
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPassError("");
    setPassSuccess("");

    if (!actualPass || !nuevaPass) {
      setPassError("Todos los campos de contraseña son requeridos.");
      return;
    }
    if (nuevaPass.length < 8) {
      setPassError("La nueva contraseña debe tener al menos 8 caracteres.");
      return;
    }
    if (nuevaPass !== confirmarPass) {
      setPassError("Las contraseñas no coinciden.");
      return;
    }

    setGuardandoPass(true);
    try {
      await changePasswordRequest(actualPass, nuevaPass);
      setPassSuccess("¡Contraseña actualizada exitosamente!");
      setActualPass("");
      setNuevaPass("");
      setConfirmarPass("");
      setTimeout(() => setCambiandoPass(false), 2000);
    } catch (err) {
      setPassError(err?.response?.data?.error || "Error al actualizar la contraseña.");
    } finally {
      setGuardandoPass(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Tarjeta de Perfil del Padre de Familia */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs space-y-4">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-red-600 to-rose-500 text-white font-black text-2xl flex items-center justify-center shadow-md shadow-red-500/20">
            {(usuario?.nombre || "T").charAt(0)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-black text-slate-900 leading-tight">
                {usuario?.nombre_completo || usuario?.nombre || "Tutor de Familia"}
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Tutor Legal • {estudiantes.length} estudiante(s) asignado(s)
            </p>
            <span className="inline-block mt-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
              Cuenta Activa
            </span>
          </div>
        </div>

        {/* Datos detallados */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2 border-t border-slate-100 text-xs">
          <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
            <span className="text-slate-400 block text-[10px] font-medium uppercase">Documento de Identidad</span>
            <span className="font-mono font-bold text-slate-800 text-sm mt-0.5 block">
              {usuario?.ci || "No registrado"}
            </span>
          </div>

          <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
            <span className="text-slate-400 block text-[10px] font-medium uppercase">Usuario de Acceso</span>
            <span className="font-mono font-bold text-slate-800 text-sm mt-0.5 block">
              {usuario?.usuario || usuario?.email || "Sin usuario"}
            </span>
          </div>

          <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
            <span className="text-slate-400 block text-[10px] font-medium uppercase">Correo Electrónico</span>
            <span className="font-medium text-slate-800 mt-0.5 block truncate">
              {usuario?.email || "No registrado"}
            </span>
          </div>

          <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
            <span className="text-slate-400 block text-[10px] font-medium uppercase">Correo de Notificaciones</span>
            <span className="font-medium text-slate-800 mt-0.5 block truncate">
              {usuario?.correo_personal || usuario?.email || "No registrado"}
            </span>
          </div>
        </div>
      </div>

      {/* Cambio de Contraseña */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-bold text-sm sm:text-base text-slate-900">Seguridad de la Cuenta</h3>
            <p className="text-xs text-slate-500">Mantén protegidas las credenciales de acceso</p>
          </div>
          <button
            onClick={() => setCambiandoPass(!cambiandoPass)}
            className="text-xs font-semibold text-red-600 hover:text-red-700 px-3 py-1.5 rounded-lg border border-red-200 bg-red-50 transition"
          >
            {cambiandoPass ? "Cancelar" : "Cambiar Contraseña"}
          </button>
        </div>

        {cambiandoPass && (
          <form onSubmit={handleChangePassword} className="space-y-3 pt-3 border-t border-slate-100 text-xs">
            {passError && (
              <div className="p-2.5 bg-red-50 border border-red-200 rounded-xl text-red-700 text-xs">
                {passError}
              </div>
            )}
            {passSuccess && (
              <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-700 text-xs font-semibold">
                {passSuccess}
              </div>
            )}

            <div>
              <label className="block text-slate-600 font-semibold mb-1">Contraseña Actual:</label>
              <input
                type="password"
                value={actualPass}
                onChange={(e) => setActualPass(e.target.value)}
                placeholder="Ingresa tu contraseña actual"
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs focus:outline-none focus:border-red-500"
              />
            </div>

            <div>
              <label className="block text-slate-600 font-semibold mb-1">Nueva Contraseña (mínimo 8 caracteres):</label>
              <input
                type="password"
                value={nuevaPass}
                onChange={(e) => setNuevaPass(e.target.value)}
                placeholder="Nueva contraseña segura"
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs focus:outline-none focus:border-red-500"
              />
            </div>

            <div>
              <label className="block text-slate-600 font-semibold mb-1">Confirmar Nueva Contraseña:</label>
              <input
                type="password"
                value={confirmarPass}
                onChange={(e) => setConfirmarPass(e.target.value)}
                placeholder="Repite la nueva contraseña"
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs focus:outline-none focus:border-red-500"
              />
            </div>

            <button
              type="submit"
              disabled={guardandoPass}
              className="w-full py-2.5 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl text-xs transition disabled:opacity-50"
            >
              {guardandoPass ? "Actualizando..." : "Guardar Nueva Contraseña"}
            </button>
          </form>
        )}
      </div>

      {/* Tarjeta de Aplicación PWA Móvil */}
      <div className="bg-gradient-to-br from-red-50 to-rose-50 border border-red-200/80 rounded-2xl p-5 text-slate-800 space-y-3">
        <div className="flex items-start gap-3">
          <div className="text-3xl">📲</div>
          <div>
            <h4 className="font-bold text-sm text-red-950">
              Instala el Portal en tu Celular (PWA)
            </h4>
            <p className="text-xs text-slate-600 mt-1 leading-relaxed">
              Puedes instalar esta página como una aplicación móvil nativa en la pantalla de inicio de tu teléfono Android o iPhone.
            </p>
          </div>
        </div>

        {pwaInstallable ? (
          <button
            onClick={promptInstallPwa}
            className="w-full py-2.5 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl text-xs shadow-sm transition flex items-center justify-center gap-2"
          >
            <span>Instalar Aplicación Ahora</span>
            <span>⬇</span>
          </button>
        ) : (
          <div className="bg-white/80 rounded-xl p-3 border border-red-200/60 text-xs text-slate-700 space-y-2">
            <div className="font-semibold text-slate-800">Instrucciones según tu teléfono:</div>
            <ul className="space-y-1.5 list-disc list-inside text-[11px] text-slate-600">
              <li>
                <strong>Android (Chrome):</strong> Presiona los 3 puntos de la esquina superior derecha y selecciona <em>"Instalar aplicación"</em> o <em>"Agregar a pantalla principal"</em>.
              </li>
              <li>
                <strong>iPhone (Safari):</strong> Toca el botón <em>Compartir</em> (ícono de cuadrado con flecha hacia arriba) y selecciona <em>"Agregar al inicio"</em>.
              </li>
            </ul>
          </div>
        )}
      </div>

      {/* Botón de Cerrar Sesión */}
      <div className="pt-2">
        <button
          type="button"
          onClick={handleLogout}
          disabled={cerrandoSesion}
          className="w-full py-3 bg-white hover:bg-red-50 text-red-600 font-bold rounded-2xl text-xs border border-red-200 shadow-2xs transition flex items-center justify-center gap-2 active:scale-95 disabled:opacity-50"
        >
          <span>🚪</span>
          <span>{cerrandoSesion ? "Cerrando sesión..." : "Cerrar Sesión"}</span>
        </button>
      </div>
    </div>
  );
}
