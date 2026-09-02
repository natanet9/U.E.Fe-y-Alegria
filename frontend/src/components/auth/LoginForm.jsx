import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginRequest } from "../../services/authService";

function LoginForm() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const demoLogin = process.env.NODE_ENV !== "production";

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await loginRequest(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err?.response?.data?.error || "No se pudo iniciar sesion");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      className="w-full bg-white rounded-2xl shadow-panel p-8 md:p-10 flex flex-col gap-5"
      onSubmit={handleSubmit}
    >
      <header className="text-center">
        <h2 className="m-0 text-3xl font-semibold text-black tracking-wide">Bienvenido</h2>
        <p className="m-0 mt-2 text-base text-black/75 tracking-wide">
          Inicia sesion para continuar
        </p>
      </header>

      {error ? (
        <p className="m-0 rounded-lg bg-red-50 border border-red-200 text-red-700 px-4 py-2 text-sm">
          {error}
        </p>
      ) : null}

      <div className="flex flex-col gap-1.5">
        <label className="text-base font-medium text-black tracking-wide" htmlFor="email">
          Correo electronico
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="w-full px-4 py-3 rounded-xl border border-gray-300 bg-gray-50 text-base outline-none focus:border-brand-600 focus:bg-white transition"
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
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="w-full px-4 py-3 rounded-xl border border-gray-300 bg-gray-50 text-base outline-none focus:border-brand-600 focus:bg-white transition"
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
          className="text-left sm:text-right text-sm sm:text-base font-medium text-blue-600 hover:underline bg-transparent border-0 p-0 cursor-pointer"
        >
          Olvidaste tu contrasena?
        </button>
      </div>

      <button
        className="w-full bg-brand-600 text-white rounded-xl py-3.5 text-base font-semibold tracking-wide cursor-pointer border-none hover:bg-brand-700 transition disabled:opacity-70 disabled:cursor-not-allowed"
        type="submit"
        disabled={loading}
      >
        {loading ? "Ingresando..." : "Iniciar Sesion"}
      </button>
    </form>
  );
}

export default LoginForm;
