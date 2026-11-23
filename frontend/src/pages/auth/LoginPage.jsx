import InfoPanel from "../../components/auth/InfoPanel";
import LoginForm from "../../components/auth/LoginForm";

function LoginPage() {
  return (
    <main className="min-h-screen w-full grid grid-cols-1 lg:grid-cols-[1.35fr_0.95fr] bg-white">
      <InfoPanel />
      <LoginForm />
    </main>
  );
}

export default LoginPage;