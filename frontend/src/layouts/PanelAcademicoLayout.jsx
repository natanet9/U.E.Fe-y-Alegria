import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useState } from "react";
import { getStoredUser, logoutRequest } from "../services/authService";
import NotificationBell from "../components/notifications/NotificationBell";

const menu = [
  { to: "/dashboard", label: "Dashboard", icon: "home" },
  { to: "/estado-notas", label: "Estado de Notas", icon: "chart", rolesVisibles: ["director", "secretaria"] },
  { to: "/estudiantes", label: "Estudiantes", icon: "users", rolesVisibles: ["director", "secretaria", "regente", "docente", "tutor"] },
  { to: "/docentes", label: "Docentes", icon: "users", rolesVisibles: ["director", "secretaria", "regente"] },
  { to: "/inscripcion", label: "Inscripción", icon: "users", rolesVisibles: ["director", "secretaria"] },
  { to: "/cursos", label: "Cursos", icon: "book", rolesVisibles: ["director", "secretaria", "regente", "docente"] },
  { to: "/calificaciones", label: "Calificaciones", icon: "grade", rolesVisibles: ["director", "secretaria", "regente", "docente", "estudiante"] },
  { to: "/horarios", label: "Horarios", icon: "calendar", rolesVisibles: ["director", "secretaria", "regente", "docente"] },
  { to: "/reportes", label: "Reportes", icon: "report", rolesVisibles: ["director", "secretaria", "regente"] },
  { to: "/boletin", label: "Boletín", icon: "grade" },
  { to: "/periodos", label: "Periodos", icon: "calendar", rolesVisibles: ["director"] },
  { to: "/dimensiones", label: "Dimensiones", icon: "chart", rolesVisibles: ["director"] },
  { to: "/usuarios", label: "Usuarios", icon: "users", rolesVisibles: ["director"] },
  { to: "/licencias", label: "Licencias", icon: "report", rolesVisibles: ["director", "secretaria", "regente"] },

];

function Icon({ name, className = "w-5 h-5" }) {
  switch (name) {
    case "home":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M3 11.5L12 4l9 7.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M5 21V12h14v9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "users":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M17 21v-2a4 4 0 00-4-4H7a4 4 0 00-4 4v2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="9" cy="7" r="4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M23 21v-2a4 4 0 00-3-3.87" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "book":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M4 19.5A2.5 2.5 0 016.5 17H20" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M4 5.5A2.5 2.5 0 016.5 3H20v18H6.5A2.5 2.5 0 014 19.5V5.5z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "report":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M9 17v-6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M12 17v-10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M15 17v-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="1.5" />
        </svg>
      );
    case "calendar":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="3" y="5" width="18" height="16" rx="2" stroke="currentColor" strokeWidth="1.5" />
          <path d="M16 3v4M8 3v4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "grade":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2l3 6 6 .5-4.5 3.5L19 20l-7-4-7 4 1.5-7L2 8.5 8 8 12 2z" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "chart":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M4 20V8l4 4 4-6 4 4 4-6v16H4z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "edit":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M15.232 5.232l3.536 3.536M9 11l-3 3v3h3l8.5-8.5a2.5 2.5 0 00-3.536-3.536L9 11z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    default:
      return null;
  }
}

function PanelAcademicoLayout() {
  const usuario = getStoredUser();
  const roleRaw = usuario?.cargo || usuario?.rol || (Array.isArray(usuario?.roles) ? usuario.roles[0] : "") || "docente";
  const roleLabel = roleRaw ? `${roleRaw}`.charAt(0).toUpperCase() + `${roleRaw}`.slice(1) : "Docente";
  const isDirector = `${roleRaw}`.toLowerCase() === "director";
  const navigate = useNavigate();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  function userMenuItems() {
    return (
      <div className="absolute bottom-full left-0 right-0 mb-2 rounded-lg border bg-white shadow-lg">
        <button onClick={() => { setUserMenuOpen(false); navigate('/perfil'); }} className="block w-full rounded-t-lg px-4 py-2.5 text-left text-sm text-slate-700 hover:bg-slate-50">Perfil</button>
        <button onClick={async () => { setUserMenuOpen(false); await logoutRequest(); navigate('/login'); }} className="block w-full rounded-b-lg px-4 py-2.5 text-left text-sm text-slate-700 hover:bg-slate-50">Cerrar sesión</button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 overflow-x-hidden">
      <div className="flex min-h-screen">
        {mobileSidebarOpen && (
          <div className="fixed inset-0 z-30 bg-black/30 lg:hidden" onClick={() => setMobileSidebarOpen(false)} />
        )}

        <aside className={`fixed inset-y-0 left-0 z-40 flex flex-col bg-white shadow-md transition-all duration-300 overflow-hidden lg:inset-auto lg:z-auto lg:sticky lg:top-0 lg:h-screen lg:rounded-r-2xl ${sidebarCollapsed ? 'w-20' : 'w-72'} ${mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
          <div className="flex h-full flex-col">
            <div className={`flex-none ${sidebarCollapsed ? 'p-4 pb-0' : 'p-6 pb-0'}`}>
              <div className={`mb-6 flex items-center gap-4 ${sidebarCollapsed ? 'justify-center' : ''}`}>
                <div className={`flex-shrink-0 rounded-md bg-indigo-50 ${sidebarCollapsed ? 'p-2' : 'p-3'}`}>
                  <img src="/assets/login/logo-Colegio.png" alt="Logo" className={`flex-shrink-0 ${sidebarCollapsed ? 'h-8 w-8' : 'h-12 w-12'}`} />
                </div>
                {!sidebarCollapsed && (
                  <div>
                    <h1 className="text-lg font-bold text-slate-900">U.E.Panama</h1>
                    <p className="text-xs text-slate-400">{isDirector ? "Panel del director" : "Panel académico"}</p>
                  </div>
                )}
              </div>
            </div>

            <nav className={`flex-1 overflow-y-auto ${sidebarCollapsed ? 'px-2' : 'px-6'} ${sidebarCollapsed ? 'flex flex-col items-center' : ''}`}>
              <div className={`flex flex-col gap-2 ${sidebarCollapsed ? 'items-center' : ''}`}>
                {menu.filter((item) => {
                  if (!item.rolesVisibles) return true;
                  const userRole = (usuario?.cargo || usuario?.rol || "").toLowerCase();
                  return item.rolesVisibles.includes(userRole);
                }).map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={() => setMobileSidebarOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${sidebarCollapsed ? 'justify-center w-fit p-2' : ''} ${
                        isActive ? "bg-indigo-50 text-indigo-600" : "text-slate-700 hover:bg-slate-100"
                      }`
                    }
                    title={sidebarCollapsed ? item.label : undefined}
                  >
                    <div className="text-slate-400">
                      <Icon name={item.icon} className="w-5 h-5" />
                    </div>
                    {!sidebarCollapsed && <span>{item.label}</span>}
                  </NavLink>
                ))}
              </div>
            </nav>

            <div className={`flex-none relative ${sidebarCollapsed ? 'p-4' : 'p-6'}`}>
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className={`flex w-full items-center gap-3 rounded-lg border border-slate-100 bg-slate-50 transition hover:bg-slate-100 ${sidebarCollapsed ? 'justify-center p-2' : 'p-3'}`}
              >
                <div className={`flex flex-shrink-0 items-center justify-center rounded-full bg-slate-900 text-sm font-black text-white ${sidebarCollapsed ? 'h-8 w-8' : 'h-10 w-10'}`}>
                  {usuario ? `${usuario.nombre?.charAt(0) || ''}${usuario.primer_apellido?.charAt(0) || ''}`.toUpperCase() : 'MA'}
                </div>
                {!sidebarCollapsed && (
                  <div className="min-w-0 text-left">
                    <div className="text-sm font-semibold text-slate-900">{usuario ? `${usuario.nombre} ${usuario.primer_apellido}` : "Usuario"}</div>
                    <div className="text-xs text-slate-400">{roleLabel}</div>
                  </div>
                )}
              </button>
              {userMenuOpen && userMenuItems()}
            </div>
          </div>
        </aside>

        <div className="flex flex-1 flex-col min-w-0">
          <header className="sticky top-0 z-20 flex items-center justify-between border-b bg-white px-6 py-3">
            <div className="flex items-center gap-2">
              <button onClick={() => setMobileSidebarOpen(true)} className="rounded-md p-2 text-slate-600 hover:bg-slate-100 lg:hidden">
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <button onClick={() => setSidebarCollapsed(!sidebarCollapsed)} className="hidden rounded-md p-1.5 text-slate-400 hover:bg-slate-100 lg:block" title={sidebarCollapsed ? "Expandir menú" : "Contraer menú"}>
                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d={sidebarCollapsed ? "M13 17l5-5-5-5" : "M11 17l-5-5 5-5"} />
                </svg>
              </button>
            </div>

            <div className="flex items-center gap-4">
              <NotificationBell />
            </div>
          </header>

          <main className="p-4 sm:p-6 overflow-x-hidden">
            <div className="mx-auto max-w-7xl">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

export default PanelAcademicoLayout;
