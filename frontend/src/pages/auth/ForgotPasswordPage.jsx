import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  forgotPasswordRequest,
  verifyResetCodeRequest,
  resetPasswordRequest,
} from "../../services/authService";

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

function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [paso, setPaso] = useState(1);
  const [email, setEmail] = useState("");
  const [codigo, setCodigo] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPass, setNewPass] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);

  const enviarCodigo = async (event) => {
    event.preventDefault();
    setError("");
    setInfo("");
    const correo = email.trim().toLowerCase();
    if (!correo) {
      setError("Debe ingresar tu correo electronico");
      return;
    }

    setLoading(true);
    try {
      const data = await forgotPasswordRequest(correo);
      setEmail(correo);
      setInfo(
        data?.codigo_enviado
          ? `Enviamos un codigo de verificacion a ${data.destinatario || correo}. Revisa tu correo.`
          : "Si el correo esta registrado, recibiras un codigo de recuperacion en tu correo.",
      );
      setPaso(2);
    } catch (err) {
      setError(err?.response?.data?.error || "No se pudo enviar el codigo de recuperacion");
    } finally {
      setLoading(false);
    }
  };

  const verificarCodigo = async (event) => {
    event.preventDefault();
    setError("");
    setInfo("");
    if (codigo.length !== 6) {
      setError("El codigo debe tener 6 digitos");
      return;
    }

    setLoading(true);
    try {
      const data = await verifyResetCodeRequest(email, codigo);
      if (data?.reset_token) {
        setResetToken(data.reset_token);
      }
      setInfo("Codigo verificado. Define tu nueva contrasena.");
      setPaso(3);
    } catch (err) {
      setError(err?.response?.data?.error || "Codigo incorrecto o expirado");
    } finally {
      setLoading(false);
    }
  };

  const cambiarPassword = async (event) => {
    event.preventDefault();
    setError("");
    setInfo("");
    const validacion = validarPassword(newPass, confirm);
    if (validacion) {
      setError(validacion);
      return;
    }

    setLoading(true);
    try {
      await resetPasswordRequest({
        email,
        codigo,
        token: resetToken,
        newPassword: newPass,
      });
      setInfo("Contrasena actualizada. Redirigiendo al inicio de sesion...");
      setTimeout(() => navigate("/login", { replace: true }), 900);
    } catch (err) {
      setError(err?.response?.data?.error || "No se pudo actualizar la contrasena");
    } finally {
      setLoading(false);
    }
  };

  const titulos = {
    1: "Recupera tu contrasena",
    2: "Verifica el codigo",
    3: "Define tu nueva contrasena",
  };

  return (
    <main className="min-h-screen w-full bg-gray-100 flex items-center justify-center px-4 py-10">
      <section className="w-full max-w-xl bg-white rounded-2xl shadow-panel p-8 md:p-10 flex flex-col gap-5">
        <header className="text-center">
          <h1 className="m-0 text-3xl font-semibold text-black tracking-wide">{titulos[paso]}</h1>
          <p className="m-0 mt-2 text-base text-black/75">
            {paso === 1
              ? "Ingresa tu correo y te enviaremos un codigo de recuperacion."
              : paso === 2
                ? "Escribe el codigo de 6 digitos que enviamos a tu correo."
                : "Debe contener mayuscula, minuscula, numero y caracter especial."}
          </p>
        </header>

        {error ? (
          <p className="m-0 rounded-lg bg-red-50 border border-red-200 text-red-700 px-4 py-2 text-sm">{error}</p>
        ) : null}
        {info ? (
          <p className="m-0 rounded-lg bg-blue-50 border border-blue-200 text-blue-700 px-4 py-2 text-sm">{info}</p>
        ) : null}

        {paso === 1 ? (
          <form className="flex flex-col gap-4" onSubmit={enviarCodigo}>
            <div className="flex flex-col gap-1.5">
              <label className="text-base font-medium text-black" htmlFor="email">
                Correo electronico
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={inputClass}
                placeholder="tu@correo.com"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-brand-600 text-white rounded-xl py-3.5 text-base font-semibold hover:bg-brand-700 transition disabled:opacity-70"
            >
              {loading ? "Enviando..." : "Enviar codigo"}
            </button>
          </form>
        ) : null}

        {paso === 2 ? (
          <form className="flex flex-col gap-4" onSubmit={verificarCodigo}>
            <div className="flex flex-col gap-1.5">
              <label className="text-base font-medium text-black" htmlFor="codigo">
                Codigo de verificacion
              </label>
              <input
                id="codigo"
                type="text"
                inputMode="numeric"
                required
                value={codigo}
                onChange={(e) => setCodigo(e.target.value.replace(/\D/g, ""))}
                className={`${inputClass} tracking-[0.5em] text-center text-xl`}
                placeholder="000000"
              />
            </div>
            <button
              type="submit"
              disabled={loading || codigo.length !== 6}
              className="w-full bg-brand-600 text-white rounded-xl py-3.5 text-base font-semibold hover:bg-brand-700 transition disabled:opacity-70"
            >
              {loading ? "Verificando..." : "Verificar codigo"}
            </button>
            <button
              type="button"
              onClick={() => setPaso(1)}
              className="text-sm font-medium text-black/60 hover:underline bg-transparent border-0 p-0 cursor-pointer"
            >
              Usar otro correo
            </button>
          </form>
        ) : null}

        {paso === 3 ? (
          <form className="flex flex-col gap-4" onSubmit={cambiarPassword}>
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
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-brand-600 text-white rounded-xl py-3.5 text-base font-semibold hover:bg-brand-700 transition disabled:opacity-70"
            >
              {loading ? "Actualizando..." : "Cambiar contrasena"}
            </button>
          </form>
        ) : null}

        <button
          type="button"
          onClick={() => navigate("/login")}
          className="text-sm font-medium text-black/60 hover:underline bg-transparent border-0 p-0 cursor-pointer"
        >
          Volver al inicio de sesion
        </button>
      </section>
    </main>
  );
}

export default ForgotPasswordPage;