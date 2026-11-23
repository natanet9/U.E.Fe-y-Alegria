import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginRequest, verifyOtpRequest, resendOtpRequest } from "../../services/authService";

const PERFILES = [
  { id: "docente", label: "Docente", placeholder: "docente@feyalegria.edu.bo" },
  { id: "tutor", label: "Padre/Tutor", placeholder: "tutor@correo.com" },
  { id: "admin", label: "Admin", placeholder: "admin@feyalegria.edu.bo" },
];

function LoginForm() {
  const navigate = useNavigate();
  const [perfil, setPerfil] = useState("estudiante");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [codigo, setCodigo] = useState("");
  const [challenge, setChallenge] = useState(null);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);

  const perfilActual = PERFILES.find((p) => p.id === perfil) || PERFILES[0];

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
    <section className="min-h-screen w-full bg-white flex flex-col justify-between px-6 py-7 sm:px-12 lg:px-14 lg:py-9">
      {/* Barra superior de estado */}
      <div className="flex items-center justify-between gap-3 text-xs text-slate-500">
        <div className="inline-flex items-center gap-1.5 font-medium text-slate-600">
          <svg
            className="w-4 h-4 text-[#0f2338]"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M12.516 2.17a.75.75 0 00-1.032 0 11.209 11.209 0 01-7.877 3.08.75.75 0 00-.722.515A12.74 12.74 0 002.25 9.75c0 5.942 4.064 10.933 9.563 12.348a.749.749 0 00.374 0c5.499-1.415 9.563-6.406 9.563-12.348 0-1.39-.223-2.73-.635-3.985a.75.75 0 00-.722-.516l-.143.001c-2.996 0-5.717-1.17-7.734-3.08zm3.094 8.016a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z"
              clipRule="evenodd"
            />
          </svg>
        </div>

        <div className="inline-flex items-center gap-2">
          <span className="text-slate-400">Gestión:</span>
          <span className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1 font-semibold text-slate-700">
            2026
          </span>
        </div>
      </div>

      {/* Contenedor central del formulario */}
      <form
        className="my-auto w-full max-w-[430px] mx-auto py-8 flex flex-col gap-5"
        onSubmit={handleSubmit}
      >
        <header>
          <h2 className="m-0 font-serif text-3xl sm:text-[34px] font-bold text-slate-900 tracking-tight">
            {challenge ? "Verificación en dos pasos" : "Iniciar Sesión"}
          </h2>
          <p className="m-0 mt-2 text-sm text-slate-500 leading-relaxed">
            {challenge
              ? "Ingresa el código de seguridad para completar tu acceso al portal."
              : "Ingresa tus credenciales para acceder a tu aula virtual y notas."}
          </p>
        </header>

        {error ? (
          <div
            role="alert"
            className="rounded-xl bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm"
          >
            {error}
          </div>
        ) : null}

        {info ? (
          <div
            role="status"
            className="rounded-xl bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 text-sm"
          >
            {info}
          </div>
        ) : null}

        {challenge ? (
          <div className="flex flex-col gap-2">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-600" htmlFor="codigo">
              Código de verificación (6 dígitos)
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
              className="w-full px-4 py-3.5 rounded-xl border border-slate-300 bg-slate-50/60 text-slate-900 font-bold tracking-[0.45em] text-center text-xl outline-none focus:border-[#0f2338] focus:bg-white focus:ring-4 focus:ring-[#0f2338]/10 transition"
              placeholder="000000"
            />
            <div className="flex items-center justify-between pt-1">
              {challenge.metodo !== "totp" ? (
                <button
                  type="button"
                  onClick={handleResend}
                  className="text-xs font-semibold text-amber-600 hover:underline bg-transparent border-0 p-0 cursor-pointer"
                >
                  Reenviar código
                </button>
              ) : (
                <span className="text-xs text-slate-500">Usa tu app autenticadora</span>
              )}
              <button
                type="button"
                onClick={volver}
                className="text-xs font-medium text-slate-500 hover:text-slate-800 bg-transparent border-0 p-0 cursor-pointer"
              >
                ← Volver
              </button>
            </div>
          </div>
        ) : (
          <>
            

            {/* Campo Correo Electrónico */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between gap-2">
                <label className="text-xs font-bold text-slate-700" htmlFor="email">
                  Correo Institucional
                </label>
                <span className="text-[11px] font-mono text-slate-400">
                  Ej. {perfilActual.placeholder}
                </span>
              </div>

              <div className="relative">
                <span className="pointer-events-none absolute inset-y-0 left-3.5 flex items-center text-slate-400">
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.8}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
                    />
                  </svg>
                </span>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="username"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-300 bg-white text-slate-900 placeholder:text-slate-400 text-sm outline-none focus:border-[#0f2338] focus:ring-4 focus:ring-[#0f2338]/10 transition"
                  placeholder="Ingrese su correo electrónico"
                />
              </div>
            </div>

            {/* Campo Contraseña */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between gap-2">
                <label className="text-xs font-bold text-slate-700" htmlFor="password">
                  Contraseña
                </label>
                <button
                  type="button"
                  onClick={() => navigate("/recuperar-contrasena")}
                  className="text-xs font-semibold text-slate-600 hover:text-slate-900 hover:underline bg-transparent border-0 p-0 cursor-pointer"
                >
                  ¿Olvidaste tu contraseña?
                </button>
              </div>

              <div className="relative">
                <span className="pointer-events-none absolute inset-y-0 left-3.5 flex items-center text-slate-400">
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.8}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"
                    />
                  </svg>
                </span>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="w-full pl-10 pr-10 py-3 rounded-xl border border-slate-300 bg-white text-slate-900 placeholder:text-slate-400 text-sm outline-none focus:border-[#0f2338] focus:ring-4 focus:ring-[#0f2338]/10 transition"
                  placeholder="••••••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                  className="absolute inset-y-0 right-3 flex items-center text-slate-400 hover:text-slate-700 bg-transparent border-0 p-1 cursor-pointer"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.8}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                </button>
              </div>
            </div>

            <label className="inline-flex items-center gap-2.5 cursor-pointer text-xs sm:text-sm text-slate-600 select-none">
              <input
                className="w-4 h-4 rounded border-slate-300 accent-[#0f2338] cursor-pointer"
                type="checkbox"
                name="remember"
              />
              Mantener sesión iniciada en este equipo
            </label>
          </>
        )}

        <button
          className="mt-1 w-full inline-flex items-center justify-center gap-2 bg-[#0f2338] hover:bg-[#173350] text-white rounded-xl py-3.5 px-5 text-sm font-semibold tracking-wide cursor-pointer border-none shadow-md shadow-slate-900/15 active:scale-[0.99] transition disabled:opacity-65 disabled:cursor-not-allowed"
          type="submit"
          disabled={loading || (challenge ? codigo.length !== 6 : false)}
        >
          {loading ? (
            <span>Verificando...</span>
          ) : (
            <>
              <span>{challenge ? "Verificar Código" : "Ingresar al Portal"}</span>
              <span aria-hidden="true">→</span>
            </>
          )}
        </button>
      </form>

      {/* Pie de página discreto */}
      <footer className="text-center text-xs text-slate-400">
        © 2026 Fe y Alegría · Todos los derechos reservados
      </footer>
    </section>
  );
}

export default LoginForm;