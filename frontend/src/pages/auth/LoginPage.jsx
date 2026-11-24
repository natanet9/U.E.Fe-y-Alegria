import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import InfoPanel from "../../components/auth/InfoPanel";
import LoginForm from "../../components/auth/LoginForm";
import { isAuthenticated, getStoredUser } from "../../services/authService";

function LoginPage() {
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated()) {
      const user = getStoredUser();
      const role = (user?.rol || user?.cargo || "").toLowerCase();
      if (role === "tutor") {
        navigate("/padres", { replace: true });
      } else {
        navigate("/dashboard", { replace: true });
      }
    }
  }, [navigate]);

  return (
    <main className="min-h-screen w-full grid grid-cols-1 lg:grid-cols-[1.35fr_0.95fr] bg-white">
      <InfoPanel />
      <LoginForm />
    </main>
  );
}

export default LoginPage;