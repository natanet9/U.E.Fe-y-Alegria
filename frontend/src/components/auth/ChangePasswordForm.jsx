import { useState } from "react";
import { changePasswordRequest } from "../../services/authService";

function ChangePasswordForm() {
  const [current, setCurrent] = useState("");
  const [newPass, setNewPass] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const validate = () => {
    if (!current || !newPass) return "Debe completar contraseña actual y nueva";
    if (newPass !== confirm) return "La contraseña nueva y la confirmación no coinciden";
    if (newPass.length < 8) return "La contraseña debe tener al menos 8 caracteres";
    const hasUpper = /[A-Z]/.test(newPass);
    const hasLower = /[a-z]/.test(newPass);
    const hasNumber = /[0-9]/.test(newPass);
    const hasSpecial = /[!@#$%^&*]/.test(newPass);
    if (!(hasUpper && hasLower && hasNumber && hasSpecial)) {
      return "La contraseña debe incluir mayúscula, minúscula, número y carácter especial";
    }
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    const v = validate();
    if (v) {
      setError(v);
      return;
    }

    setLoading(true);
    try {
      await changePasswordRequest(current, newPass);
      setSuccess("Contraseña actualizada");
      setCurrent("");
      setNewPass("");
      setConfirm("");
    } catch (err) {
      setError(err?.response?.data?.error || "No se pudo cambiar la contraseña");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="w-full bg-white rounded-2xl shadow-panel p-8 md:p-10 flex flex-col gap-5" onSubmit={handleSubmit}>
      <header className="text-center">
        <h2 className="m-0 text-2xl font-semibold text-black tracking-wide">Cambiar contraseña</h2>
        <p className="m-0 mt-2 text-sm text-black/75">Ingresa tu contraseña actual y la nueva</p>
      </header>

      {error ? <p className="m-0 rounded-lg bg-red-50 border border-red-200 text-red-700 px-4 py-2 text-sm">{error}</p> : null}
      {success ? <p className="m-0 rounded-lg bg-green-50 border border-green-200 text-green-700 px-4 py-2 text-sm">{success}</p> : null}

      <div className="flex flex-col gap-1.5">
        <label className="text-base font-medium text-black tracking-wide">Contraseña actual</label>
        <input type="password" value={current} onChange={(e) => setCurrent(e.target.value)} className="w-full px-4 py-3 rounded-xl border border-gray-300 bg-gray-50 text-base outline-none focus:border-brand-600 focus:bg-white transition" />
      </div>

      <div className="flex flex-col gap-1.5">
        <label className="text-base font-medium text-black tracking-wide">Contraseña nueva</label>
        <input type="password" value={newPass} onChange={(e) => setNewPass(e.target.value)} className="w-full px-4 py-3 rounded-xl border border-gray-300 bg-gray-50 text-base outline-none focus:border-brand-600 focus:bg-white transition" />
      </div>

      <div className="flex flex-col gap-1.5">
        <label className="text-base font-medium text-black tracking-wide">Confirmar contraseña</label>
        <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} className="w-full px-4 py-3 rounded-xl border border-gray-300 bg-gray-50 text-base outline-none focus:border-brand-600 focus:bg-white transition" />
      </div>

      <button type="submit" className="w-full bg-brand-600 text-white rounded-xl py-3.5 text-base font-semibold tracking-wide" disabled={loading}>
        {loading ? "Actualizando..." : "Actualizar contraseña"}
      </button>
    </form>
  );
}

export default ChangePasswordForm;
