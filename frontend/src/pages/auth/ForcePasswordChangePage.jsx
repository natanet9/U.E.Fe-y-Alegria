import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { changePasswordRequest, getStoredUser } from "../../services/authService";

const inputClass =
  "w-full px-4 py-3 rounded-xl border border-gray-300 bg-gray-50 text-base outline-none focus:border-brand-600 focus:bg-white transition";

function validarPassword(newPass, confirm) {
  if (!newPass) return "Debe ingresar la nueva contrasena";
  if (newPass.length < 8) return "La contrasena debe tener al menos 8 caracteres";
  if (!/[A-Z]/.test(newPass)) return "Debe incluir al menos una letra mayuscula";
  if (!/[a-z]/.test(newPass)) return "Debe incluir al menos una letra minuscula";
  if (!/[0-9]/.test(newPass)) return "Debe incluir al menos un numero";
  if (!/[^A-Za-z0-9]/.test(newPass)) return "Debe incluir al menos un caracter especial";
  if (newPass !== confirm) return "La contrasena nueva y la confirmacion no coinciden";
  return null;
}

function ForcePasswordChangePage() {
  const navigate = useNavigate();
  const [current, setCurrent] = useState("");
  const [newPass, setNewPass] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const usuario = getStoredUser();

  useEffect(() => {
    if (!usuario) {
      navigate("/login", { replace: true });
    }
  }, [usuario, navigate]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    const validacion = validarPassword(newPass, confirm);
    if (validacion) {
      setError(validacion);
      return;
    }

    setLoading(true);
    try {
      await changePasswordRequest(current, newPass);
      setSuccess("Contrasena actualizada. Redirigiendo...");
      setTimeout(() => navigate("/dashboard", { replace: true }), 900);
    } catch (err) {
      setError(err?.response?.data?.error || "No se pudo cambiar la contrasena");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen w-full bg-gray-100 flex items-center justify-center px-4 py-10">
      <section className="w-full max-w-xl bg-white rounded-2xl shadow-panel p-8 md:p-10 flex flex-col gap-5">
        <header className="text-center">
          <h1 className="m-0 text-3xl font-semibold text-black tracking-wide">Cambia tu contrasena</h1>
          <p className="m-0 mt-2 text-base text-black/75">
            Tu contrasena es temporal. Debes cambiarla para continuar usando el sistema.
          </p>
        </header>

        {error ? (
          <p className="m-0 rounded-lg bg-red-50 border border-red-200 text-red-700 px-4 py-2 text-sm">{error}</p>
        ) : null}
        {success ? (
          <p className="m-0 rounded-lg bg-green-50 border border-green-200 text-green-700 px-4 py-2 text-sm">{success}</p>
        ) : null}

        <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
          <div className="flex flex-col gap-1.5">
            <label className="text-base font-medium text-black" htmlFor="current">
              Contrasena temporal (actual)
            </label>
            <input
              id="current"
              type="password"
              required
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
              className={inputClass}
              placeholder="La contrasena que recibiste por correo"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-base font-medium text-black" htmlFor="nueva">
              Nueva contrasena
            </label>
            <input
              id="nueva"
              type="password"
              required
              value={newPass}
              onChange={(e) => setNewPass(e.target.value)}
              className={inputClass}
              placeholder="Minimo 8 caracteres"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-base font-medium text-black" htmlFor="confirmar">
              Confirmar contrasena
            </label>
            <input
              id="confirmar"
              type="password"
              required
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              className={inputClass}
              placeholder="Repite la contrasena nueva"
            />
          </div>

          <p className="m-0 text-sm text-black/60">
            Debe contener mayuscula, minuscula, numero y caracter especial.
          </p>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-600 text-white rounded-xl py-3.5 text-base font-semibold hover:bg-brand-700 transition disabled:opacity-70"
          >
            {loading ? "Actualizando..." : "Cambiar contrasena"}
          </button>
        </form>
      </section>
    </main>
  );
}

export default ForcePasswordChangePage;