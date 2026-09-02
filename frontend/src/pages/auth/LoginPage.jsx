import InfoPanel from "../../components/auth/InfoPanel";
import LoginForm from "../../components/auth/LoginForm";

function LoginPage() {
  return (
    <main className="min-h-screen w-full bg-gray-100 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-[1fr_460px] gap-6">
        <InfoPanel />
        <section className="flex flex-col gap-4 justify-center">
          <LoginForm />
          <p className="text-center text-sm font-medium text-black/50 tracking-wide">
            Copyright 2026 U.E.Panama. Todos los derechos reservados.
          </p>
        </section>
      </div>
    </main>
  );
}

export default LoginPage;
