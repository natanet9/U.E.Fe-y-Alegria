import React, { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { PadresProvider, usePadres } from "../context/PadresContext";
import { logoutRequest } from "../services/authService";
import StudentSelector from "../components/padres/StudentSelector";
import ChatbotModal from "../components/padres/ChatbotModal";

function PadresLayoutContent() {
  const { setChatbotOpen, setUsuario, pwaInstallable, promptInstallPwa, estudianteActivo } = usePadres();
  const location = useLocation();
  const navigate = useNavigate();
  const [cerrandoSesion, setCerrandoSesion] = useState(false);

  const handleLogout = async () => {
    if (cerrandoSesion) return;
    setCerrandoSesion(true);
    try {
      await logoutRequest();
      setUsuario?.(null);
    } finally {
      navigate("/padres/login", { replace: true });
    }
  };

  // Bottom Navigation tabs definition
  const navTabs = [
    {
      to: "/padres",
      end: true,
      label: "Inicio",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
          />
        </svg>
      ),
    },
    {
      to: "/padres/calificaciones",
      label: "Calificaciones",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      ),
    },
    {
      to: "/padres/asistencia",
      label: "Asistencia",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
      ),
    },
    {
      to: "/padres/licencia",
      label: "Licencia",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      ),
    },
    {
      to: "/padres/perfil",
      label: "Mi Perfil",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
          />
        </svg>
      ),
    },
  ];

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans antialiased text-slate-800 select-none pb-20">
      {/* Top Header */}
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-slate-200/80 shadow-2xs">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-red-600 flex items-center justify-center text-white font-black text-lg shadow-sm">
              <img
                src="/assets/login/logoUEdivino.jpg"
                alt="Logo U.E. Divino Corazón de Jesús"
              />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h1 className="font-bold text-sm sm:text-base text-slate-900 tracking-tight leading-none">
                  U.E. Divino Corazón de Jesús
                </h1>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-red-100 text-red-700 leading-none">
                  FAMILIA
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5 leading-none">
                Portal de Seguimiento Escolar
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* PWA Install Button if available */}
            {pwaInstallable && (
              <button
                onClick={promptInstallPwa}
                className="hidden sm:flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 text-xs font-semibold border border-emerald-200 transition"
              >
                <span>📲 Instalar App</span>
              </button>
            )}

            {/* AI Assistant Quick Pill */}
            <button
              onClick={() => setChatbotOpen(true)}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-red-50 text-red-700 hover:bg-red-100 border border-red-200 text-xs font-semibold transition active:scale-95"
              title="Abrir Asistente Virtual"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-red-600"></span>
              </span>
              <span>Chatbot IA</span>
            </button>

            {/* Cerrar sesión rápido */}
            <button
              type="button"
              onClick={handleLogout}
              disabled={cerrandoSesion}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-xl bg-slate-100 text-slate-700 hover:bg-rose-50 hover:text-rose-700 border border-slate-200 hover:border-rose-200 text-xs font-semibold transition active:scale-95 disabled:opacity-50"
              title="Cerrar sesión"
              aria-label="Cerrar sesión"
            >
              <span>Salir</span>
            </button>
          </div>
        </div>

        {/* Student Switcher strip (shown under header on non-perfil routes) */}
        {location.pathname !== "/padres/perfil" && (
          <div className="max-w-2xl mx-auto px-4 pb-2.5">
            <StudentSelector />
          </div>
        )}
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-2xl w-full mx-auto px-4 py-4 sm:py-5">
        <Outlet />
      </main>

      {/* Floating Action Button (FAB) for the Chatbot */}
      <div className="fixed bottom-20 right-4 z-40 sm:right-8">
        <button
          onClick={() => setChatbotOpen(true)}
          className="group relative flex items-center justify-center w-13 h-13 rounded-full bg-gradient-to-tr from-red-600 to-rose-500 text-white shadow-lg shadow-red-500/30 hover:scale-105 active:scale-95 transition-all duration-200 focus:outline-none"
          aria-label="Abrir Asistente Virtual IA"
        >
          <span className="text-2xl">🤖</span>
          {/* Badge indicator */}
          <span className="absolute -top-1 -right-1 flex h-4 w-4">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-4 w-4 bg-amber-500 text-[9px] font-bold text-black items-center justify-center">
              AI
            </span>
          </span>
        </button>
      </div>

      {/* Chatbot Modal */}
      <ChatbotModal />

      {/* Fixed Bottom Navigation Bar (Mobile App Style) */}
      <nav className="fixed bottom-0 inset-x-0 z-40 bg-white/95 backdrop-blur-lg border-t border-slate-200/90 shadow-lg pb-[env(safe-area-inset-bottom)]">
        <div className="max-w-md mx-auto grid grid-cols-5 h-16">
          {navTabs.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              end={tab.end}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center gap-1 transition-all text-xs font-medium ${
                  isActive
                    ? "text-red-600 scale-105 font-bold"
                    : "text-slate-500 hover:text-slate-800"
                }`
              }
            >
              <div className="transition-transform duration-150">{tab.icon}</div>
              <span className="text-[11px] leading-tight tracking-tight">{tab.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}

export default function PadresLayout() {
  return (
    <PadresProvider>
      <PadresLayoutContent />
    </PadresProvider>
  );
}
