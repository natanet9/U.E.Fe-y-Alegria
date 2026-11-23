import { useState } from "react";

const AVISOS = [
  {
    tag: "GESTIÓN 2026",
    fecha: "Portal Académico",
    titulo: "Registro de Calificaciones y Asistencia Habilitado",
    descripcion:
      "Docentes y administrativos pueden gestionar evaluaciones por dimensiones, control de asistencia y boletines oficiales en línea.",
  },
  {
    tag: "COMUNICADOS",
    fecha: "Comunidad Educativa",
    titulo: "Consulta de Horarios y Seguimiento Estudiantil",
    descripcion:
      "Accede al cronograma actualizado de materias, reportes de rendimiento académico y notificaciones institucionales.",
  },
  {
    tag: "SEGURIDAD",
    fecha: "Acceso Protegido",
    titulo: "Autenticación Institucional Verificada",
    descripcion:
      "Recuerda mantener actualizada tu contraseña y activar la verificación en dos pasos para proteger tu cuenta.",
  },
];

function InfoPanel() {
  const [indice, setIndice] = useState(0);
  const avisoActual = AVISOS[indice];

  const anterior = () => {
    setIndice((prev) => (prev === 0 ? AVISOS.length - 1 : prev - 1));
  };

  const siguiente = () => {
    setIndice((prev) => (prev === AVISOS.length - 1 ? 0 : prev + 1));
  };

  return (
    <section className="relative min-h-[380px] lg:min-h-screen w-full overflow-hidden bg-[#0c1d2e] text-white flex flex-col justify-between p-7 sm:p-10 lg:px-14 lg:py-11">
      {/* Imagen de fondo con tratamiento editorial oscuro */}
      <img
        src="/assets/login/students.png"
        alt="Estudiantes en aula"
        className="absolute inset-0 h-full w-full object-cover object-center opacity-30 scale-105"
      />
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-gradient-to-br from-[#091726]/95 via-[#0f2338]/88 to-[#2a1218]/85"
      />

      {/* Barra superior institucional */}
      <header className="relative z-10 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="h-12 w-12 rounded-xl bg-white/10 backdrop-blur-md border border-white/15 p-2 flex items-center justify-center shadow-sm background:white/5">
            <img
              className="h-full w-full object-contain"
              alt="Logo U.E. Divino Corazón de Jesús"
              src="/assets/login/logoUEdivino.jpg"
            />
          </div>
          <div>
            <p className="m-0 text-[11px] font-bold uppercase tracking-[0.14em] text-amber-400">
              Educación Popular <span className="text-white/40 mx-1">•</span>{" "}
              <span className="text-slate-300 font-medium normal-case tracking-normal">
                Excelencia Académica
              </span>
            </p>
            <span className="block font-serif text-xl sm:text-2xl font-bold tracking-tight text-white mt-0.5">
              U.E. Divino Corazón de Jesús
            </span>
          </div>
        </div>

        <div className="inline-flex items-center gap-2 rounded-full bg-white/10 backdrop-blur-md border border-white/15 px-3.5 py-1.5 text-xs font-medium text-slate-200">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          Servicios en línea
        </div>
      </header>

      {/* Bloque central editorial */}
      <div className="relative z-10 my-10 lg:my-auto max-w-xl">
        <div className="inline-flex items-center gap-2 rounded-full bg-amber-500/15 border border-amber-400/30 px-3.5 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-amber-300 mb-5">
          <span>✦</span>
          <span>Ecosistema Educativo Integral</span>
        </div>

        <h1 className="m-0 font-serif text-3xl sm:text-5xl lg:text-[52px] font-bold leading-[1.12] tracking-tight text-white">
          Formando líderes con{" "}
          <span className="italic text-amber-400">conciencia, ciencia</span> y valores.
        </h1>

        <p className="m-0 mt-5 text-sm sm:text-base lg:text-[17px] text-slate-300 leading-relaxed max-w-lg">
          Bienvenido al portal unificado de gestión académica. Acceda a calificaciones,
          planificación curricular, comunicación institucional y servicios administrativos en un
          entorno seguro.
        </p>
      </div>

      {/* Tarjeta inferior tipo glassmorphism */}
      <div className="relative z-10 hidden sm:block max-w-xl">
        <div className="rounded-2xl bg-white/[0.08] backdrop-blur-md border border-white/15 p-5 shadow-xl">
          <div className="flex items-center justify-between gap-3 mb-2.5">
            <div className="flex items-center gap-3">
              <span className="rounded-md bg-amber-500 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-950">
                {avisoActual.tag}
              </span>
              <span className="text-xs font-medium text-slate-300">{avisoActual.fecha}</span>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={anterior}
                aria-label="Aviso anterior"
                className="h-7 w-7 rounded-full bg-white/10 hover:bg-white/20 border border-white/15 flex items-center justify-center text-white transition cursor-pointer"
              >
                ‹
              </button>
              <button
                type="button"
                onClick={siguiente}
                aria-label="Siguiente aviso"
                className="h-7 w-7 rounded-full bg-white/10 hover:bg-white/20 border border-white/15 flex items-center justify-center text-white transition cursor-pointer"
              >
                ›
              </button>
            </div>
          </div>

          <h3 className="m-0 text-sm sm:text-base font-bold text-white">
            {avisoActual.titulo}
          </h3>
          <p className="m-0 mt-1 text-xs sm:text-sm text-slate-300 leading-relaxed">
            {avisoActual.descripcion}
          </p>
        </div>
      </div>
    </section>
  );
}

export default InfoPanel;