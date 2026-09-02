import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { getStoredUser, getCurrentUser, isAuthenticated } from "../../services/authService";

function ProtectedRoute({ children, allowedRoles = [] }) {
  const [checking, setChecking] = useState(true);
  const [valid, setValid] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function verifySession() {
      if (!isAuthenticated()) {
        setChecking(false);
        setValid(false);
        return;
      }

      try {
        const usuario = await getCurrentUser();
        if (!cancelled) {
          // Update stored user data in case it changed
          localStorage.setItem("auth_user", JSON.stringify(usuario));
          setValid(true);
          setChecking(false);
        }
      } catch {
        if (!cancelled) {
          // Cookie expired or invalid – clean up
          localStorage.removeItem("auth_user");
          setValid(false);
          setChecking(false);
        }
      }
    }

    verifySession();

    return () => {
      cancelled = true;
    };
  }, []);

  if (checking) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Verificando sesión...</div>
      </div>
    );
  }

  if (!valid) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles.length) {
    const usuario = getStoredUser();
    const userRoles = new Set(
      [usuario?.cargo, usuario?.rol, ...(Array.isArray(usuario?.roles) ? usuario.roles : [])]
        .filter(Boolean)
        .map((role) => `${role}`.toLowerCase()),
    );

    const allowed = allowedRoles.some((role) => userRoles.has(`${role}`.toLowerCase()));
    if (!allowed) {
      return <Navigate to="/dashboard" replace />;
    }
  }

  return children;
}

export default ProtectedRoute;