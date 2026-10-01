import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginRequest, verifyOtpRequest, resendOtpRequest } from "../../services/authService";

const inputClass =
  "w-full px-4 py-3 rounded-xl border border-gray-300 bg-gray-50 text-base outline-none focus:border-brand-600 focus:bg-white transition";

function LoginForm() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [codigo, setCodigo] = useState("");
  const [challenge, setChallenge] = useState(null);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);

  const afterLogin = (usuario) => {
    if (usuario?.debe_cambiar_password) {
      navigate("/cambiar-password-obligatorio");
      return;
    }
    navigate("/dashboard");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setInfo("");
    setLoading(true);

    try {
      if (challenge) {
        const usuario = await verifyOtpRequest(challenge.otp_token, codigo);
        afterLogin(usuario);
        return;
      }

      const data = await loginRequest(email, password);

      if (data?.requires_otp) {
        setChallenge(data);
        setCodigo("");
        setInfo(
          data.metodo === "totp"
            ? "Ingresa el codigo de 6 digitos de tu aplicacion autenticadora."
            : `Enviamos un codigo de verificacion a ${data.destinatario || "tu correo"}.`,
        );
        return;
      }

      afterLogin(data);
    } catch (err) {
      setError(err?.response?.data?.error || "No se pudo iniciar sesion");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (!challenge?.otp_token) return;
    setError("");
    setInfo("");
    setLoading(true);
    try {
      const data = await resendOtpRequest(challenge.otp_token);
      setInfo(`Codigo reenviado a ${data?.destinatario || "tu correo"}.`);
    } catch (err) {
      setError(err?.response?.data?.error || "No se pudo reenviar el codigo");
    } finally {
      setLoading(false);
    }
  };

  const volver = () => {
    setChallenge(null);
    setCodigo("");
    setError("");
    setInfo("");
  };

  return (
    <form
      className="w-full bg-white rounded-2xl shadow-panel p-8 md:p-10 flex flex-col gap-5"
      onSubmit={handleSubmit}
    >
      <header className="text-center">
        <h2 className="m-0 text-3xl font-semibold text-black tracking-wide">Bienvenido</h2>
        <p className="m-0 mt-2 text-base text-black/75 tracking-wide">
          {challenge ? "Verificacion en dos pasos" : "Inicia sesion para continuar"}
        </p>
      </header>

      {error ? (
        <p className="m-0 rounded-lg bg-red-50 border border-red-200 text-red-700 px-4 py-2 text-sm">
          {error}
        </p>
      ) : null}

      {info ? (
        <p className="m-0 rounded-lg bg-blue-50 border border-blue-200 text-blue-700 px-4 py-2 text-sm">
          {info}
        </p>
      ) : null}

      {challenge ? (
        <div className="flex flex-col gap-1.5">
          <label className="text-base font-medium text-black tracking-wide" htmlFor="codigo">
            Codigo de verificacion
          </label>
          <input
            id="codigo"
            name="codigo"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            required
            value={codigo}
            onChange={(event) => setCodigo(event.target.value.replace(/\D/g, ""))}
            className={`${inputClass} tracking-[0.5em] text-center text-xl`}
            placeholder="000000"
          />
          <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
            {challenge.metodo !== "totp" ? (
              <button
                type="button"
                onClick={handleResend}
                className="text-sm font-medium text-blue-600 hover:underline bg-transparent border-0 p-0 cursor-pointer"
              >
                Reenviar codigo
              </button>
            ) : (
              <span className="text-sm text-black/60">Usa tu aplicacion autenticadora</span>
            )}
            <button
              type="button"
              onClick={volver}
              className="text-sm font-medium text-black/60 hover:underline bg-transparent border-0 p-0 cursor-pointer"
            >
              Volver
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="flex flex-col gap-1.5">
            <label className="text-base font-medium text-black tracking-wide" htmlFor="email">
              Correo electronico
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className={inputClass}
              placeholder="tu@correo.com"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-base font-medium text-black tracking-wide" htmlFor="password">
              Contrasena
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className={inputClass}
              placeholder="********"
            />
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <label className="inline-flex items-center gap-2 cursor-pointer text-sm sm:text-base font-medium text-black tracking-wide">
              <input className="w-4 h-4" type="checkbox" name="remember" />
              Recordarme
            </label>

            <button
              type="button"
              onClick={() => navigate("/recuperar-contrasena")}
              className="text-left sm:text-right text-sm sm:text-base font-medium text-blue-600 hover:underline bg-transparent border-0 p-0 cursor-pointer"
            >
              Olvidaste tu contrasena?
            </button>
          </div>
        </>
      )}

      <button
        className="w-full bg-brand-600 text-white rounded-xl py-3.5 text-base font-semibold tracking-wide cursor-pointer border-none hover:bg-brand-700 transition disabled:opacity-70 disabled:cursor-not-allowed"
        type="submit"
        disabled={loading || (challenge ? codigo.length !== 6 : false)}
      >
        {loading ? "Verificando..." : challenge ? "Verificar codigo" : "Iniciar Sesion"}
      </button>
    </form>
  );
}

export default LoginForm;
