import { Navigate, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import { getStoredUser, logoutRequest } from "../services/authService";
import NotificationBell from "../components/notifications/NotificationBell";
import AssistantBubble from "../components/auth/AssistantBubble";

const menu = [
  { to: "/dashboard", label: "Dashboard", icon: "home" },
  { to: "/estado-notas", label: "Estado de Notas", icon: "chart", rolesVisibles: ["director", "secretaria"] },
  { to: "/estudiantes", label: "Estudiantes", icon: "users", rolesVisibles: ["director", "secretaria", "regente", "docente", "tutor"] },
  { to: "/docentes", label: "Docentes", icon: "users", rolesVisibles: ["director", "secretaria", "regente"] },
  { to: "/inscripcion", label: "Inscripción", icon: "users", rolesVisibles: ["director", "secretaria"] },
  { to: "/tutores", label: "Padres / Tutores", icon: "users", rolesVisibles: ["director", "secretaria"] },
  { to: "/cursos", label: "Cursos", icon: "book", rolesVisibles: ["director", "secretaria", "regente", "docente"] },
  { to: "/mis-areas", label: "Mis Áreas", icon: "book", rolesVisibles: ["docente"] },
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
          <path d="M3 11.5L12 4l9 7.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M5 21V12h14v9" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "users":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M17 21v-2a4 4 0 00-4-4H7a4 4 0 00-4 4v2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="9" cy="7" r="4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M23 21v-2a4 4 0 00-3-3.87" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "book":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M4 19.5A2.5 2.5 0 016.5 17H20" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M4 5.5A2.5 2.5 0 016.5 3H20v18H6.5A2.5 2.5 0 014 19.5V5.5z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "report":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M9 17v-6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M12 17v-10" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M15 17v-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="1.6" />
        </svg>
      );
    case "calendar":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="3" y="5" width="18" height="16" rx="2" stroke="currentColor" strokeWidth="1.6" />
          <path d="M16 3v4M8 3v4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "grade":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2l3 6 6 .5-4.5 3.5L19 20l-7-4-7 4 1.5-7L2 8.5 8 8 12 2z" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "chart":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M4 20V8l4 4 4-6 4 4 4-6v16H4z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "edit":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M15.232 5.232l3.536 3.536M9 11l-3 3v3h3l8.5-8.5a2.5 2.5 0 00-3.536-3.536L9 11z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
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
  const roleName = `${roleRaw}`.toLowerCase();
  const isDirector = roleName === "director";
  const canUseAssistant = ["director", "secretaria", "regente", "docente", "estudiante"].includes(roleName);
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  if (roleName === "tutor") {
    return <Navigate to="/padres" replace />;
  }

  const currentMenu = menu.find((item) => location.pathname.startsWith(item.to));
  const currentSectionTitle = currentMenu?.label || "Panel Académico";

  function userMenuItems() {
    return (
      <div className="absolute bottom-full left-4 right-4 mb-2 rounded-xl border border-white/15 bg-[#0f2338] shadow-2xl overflow-hidden z-50">
        <button
          onClick={() => {
            setUserMenuOpen(false);
            navigate("/perfil");
          }}
          className="block w-full px-4 py-2.5 text-left text-sm font-medium text-slate-200 hover:bg-white/10 hover:text-white transition"
        >
          Mi Perfil
        </button>
        <div className="h-px bg-white/10" />
        <button
          onClick={async () => {
            setUserMenuOpen(false);
            await logoutRequest();
            navigate("/login");
          }}
          className="block w-full px-4 py-2.5 text-left text-sm font-medium text-amber-400 hover:bg-white/10 transition"
        >
          Cerrar sesión
        </button>
      </div>
    );
  }

  return (
    <div className="h-screen w-full overflow-hidden bg-slate-100/80 flex">
      {/* Overlay móvil */}
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-slate-950/60 backdrop-blur-xs lg:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* Sidebar estático a altura completa */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex h-screen flex-shrink-0 flex-col bg-gradient-to-b from-[#0c1d2e] via-[#0f2338] to-[#091726] text-white border-r border-white/10 shadow-xl transition-all duration-300 lg:static ${
          sidebarCollapsed ? "w-20" : "w-72"
        } ${mobileSidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}
      >
        {/* Cabecera institucional del sidebar */}
        <div className={`flex-none border-b border-white/10 ${sidebarCollapsed ? "p-4" : "px-6 py-5"}`}>
          <div className={`flex items-center gap-3.5 ${sidebarCollapsed ? "justify-center" : ""}`}>
            <div className={`flex-shrink-0 rounded-xl bg-white/10 border border-white/15 backdrop-blur-sm ${sidebarCollapsed ? "p-2" : "p-2.5"}`}>
              <img
                src="/assets/login/logoUEdivino.jpg"
                alt="Logo U.E. Divino Corazón de Jesús"
                className={`object-contain ${sidebarCollapsed ? "h-7 w-7" : "h-10 w-10"}`}
              />
            </div>
            {!sidebarCollapsed && (
              <div className="min-w-0">
                <span className="block text-[10px] font-bold uppercase tracking-[0.16em] text-amber-400">
                  Sistema Académico
                </span>
                <h1 className="m-0 font-serif text-lg font-bold tracking-tight text-white truncate">
                  Corazón de Jesús
                </h1>
                <p className="m-0 text-xs text-slate-400 truncate">
                  {isDirector ? "Panel del Director" : `Panel · ${roleLabel}`}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Navegación con scroll propio interno si hay muchos ítems */}
        <nav className={`flex-1 overflow-y-auto py-4 ${sidebarCollapsed ? "px-2.5" : "px-4"}`}>
          {!sidebarCollapsed && (
            <p className="px-3 mb-2 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
              Menú Principal
            </p>
          )}
          <div className="flex flex-col gap-1">
            {menu
              .filter((item) => {
                if (!item.rolesVisibles) return true;
                const userRole = (usuario?.cargo || usuario?.rol || "").toLowerCase();
                return item.rolesVisibles.includes(userRole);
              })
              .map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setMobileSidebarOpen(false)}
                  className={({ isActive }) =>
                    `group flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all ${
                      sidebarCollapsed ? "justify-center px-2" : ""
                    } ${
                      isActive
                        ? "bg-amber-500 text-slate-950 font-semibold shadow-md shadow-amber-500/20"
                        : "text-slate-300 hover:bg-white/10 hover:text-white"
                    }`
                  }
                  title={sidebarCollapsed ? item.label : undefined}
                >
                  {({ isActive }) => (
                    <>
                      <span className={isActive ? "text-slate-950" : "text-slate-400 group-hover:text-amber-400 transition-colors"}>
                        <Icon name={item.icon} className="w-5 h-5" />
                      </span>
                      {!sidebarCollapsed && <span className="truncate">{item.label}</span>}
                    </>
                  )}
                </NavLink>
              ))}
          </div>
        </nav>

        {/* Tarjeta fija de usuario en la parte inferior */}
        <div className={`flex-none relative border-t border-white/10 ${sidebarCollapsed ? "p-3" : "p-4"}`}>
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className={`flex w-full items-center gap-3 rounded-xl border border-white/10 bg-white/[0.06] transition hover:bg-white/10 ${
              sidebarCollapsed ? "justify-center p-2" : "p-3"
            }`}
          >
            <div
              className={`flex flex-shrink-0 items-center justify-center rounded-full bg-amber-500 text-xs font-black text-slate-950 shadow-sm ${
                sidebarCollapsed ? "h-8 w-8" : "h-10 w-10"
              }`}
            >
              {usuario ? `${usuario.nombre?.charAt(0) || ""}${usuario.primer_apellido?.charAt(0) || ""}`.toUpperCase() : "FA"}
            </div>
            {!sidebarCollapsed && (
              <div className="min-w-0 flex-1 text-left">
                <div className="text-sm font-semibold text-white truncate">
                  {usuario ? `${usuario.nombre} ${usuario.primer_apellido}` : "Usuario"}
                </div>
                <div className="text-xs text-amber-400/90 font-medium truncate">{roleLabel}</div>
              </div>
            )}
            {!sidebarCollapsed && (
              <svg className="h-4 w-4 text-slate-400 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M8 9l4-4 4 4M16 15l-4 4-4-4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            )}
          </button>
          {userMenuOpen && userMenuItems()}
        </div>
      </aside>

      {/* Columna derecha: Header fijo + Área central con scroll independiente */}
      <div className="flex flex-1 flex-col min-w-0 h-screen overflow-hidden">
        <header className="flex-none z-20 flex items-center justify-between border-b border-slate-200/90 bg-white/95 backdrop-blur-md px-4 sm:px-6 py-3.5 shadow-xs">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileSidebarOpen(true)}
              className="rounded-xl p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
              aria-label="Abrir menú"
            >
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 6h16M4 12h16M4 18h16" strokeLinecap="round" />
              </svg>
            </button>

            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="hidden rounded-xl border border-slate-200 bg-slate-50 p-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition lg:flex items-center justify-center"
              title={sidebarCollapsed ? "Expandir menú" : "Contraer menú"}
            >
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d={sidebarCollapsed ? "M13 17l5-5-5-5M6 17l5-5-5-5" : "M11 17l-5-5 5-5M18 17l-5-5 5-5"} strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>

            <div className="hidden sm:flex items-center gap-2 text-sm">
              <span className="text-slate-400 font-medium">Portal</span>
              <span className="text-slate-300">/</span>
              <span className="font-semibold text-slate-800">{currentSectionTitle}</span>
            </div>
          </div>

          <div className="flex items-center gap-3 sm:gap-4">
            <span className="hidden md:inline-flex items-center gap-1.5 rounded-full bg-slate-100 border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Gestión {new Date().getFullYear()}
            </span>
            <NotificationBell />
          </div>
        </header>

        {/* Único contenedor con scroll vertical */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
        {canUseAssistant && <AssistantBubble />}
      </div>
    </div>
  );
}

export default PanelAcademicoLayout;