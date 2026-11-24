import React, { useMemo } from "react";
import { Link } from "react-router-dom";
import { usePadres } from "../../context/PadresContext";

export default function PadresDashboardPage() {
  const {
    usuario,
    loading,
    error,
    estudiantes,
    estudianteId,
    estudianteActivo,
    seleccionarEstudiante,
    boletin,
    boletinLoading,
    metricas,
    periodoActivo,
    descargarBoletin,
    downloading,
    setChatbotOpen,
  } = usePadres();

  // Saludo dinámico según la hora del día
  const saludoHora = useMemo(() => {
    const hora = new Date().getHours();
    if (hora < 12) return "Buenos días";
    if (hora < 19) return "Buenas tardes";
    return "Buenas noches";
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-slate-500 gap-3">
        <div className="w-12 h-12 border-4 border-red-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-semibold text-slate-700">Cargando el portal de tus hijos...</p>
        <span className="text-xs text-slate-400">U.E. Divino Corazón de Jesús</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-3xl p-6 text-red-700 text-sm space-y-2">
        <div className="font-bold flex items-center gap-2 text-base">
          <span>⚠️</span>
          <span>No se pudo cargar la información escolar</span>
        </div>
        <p className="text-xs leading-relaxed">{error}</p>
      </div>
    );
  }

  if (!estudianteActivo) {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-3xl p-8 text-amber-900 text-center space-y-3">
        <div className="text-4xl">👨‍👩‍👧‍👦</div>
        <h3 className="font-bold text-lg">Sin estudiantes asignados</h3>
        <p className="text-xs text-amber-800 max-w-sm mx-auto leading-relaxed">
          No tienes estudiantes vinculados a tu cuenta de tutor. Comunícate con la administración o secretaría del colegio para verificar la asignación con tu Carnet de Identidad (CI).
        </p>
      </div>
    );
  }

  // Lista de materias en riesgo (nota < 51)
  const materiasEnRiesgo = (boletin?.materias || []).filter(
    (m) => m.promedio_final != null && Number(m.promedio_final) < 51
  );

  // Materias con mejor nota (>= 70)
  const materiasDestacadas = (boletin?.materias || []).filter(
    (m) => m.promedio_final != null && Number(m.promedio_final) >= 70
  );

  const promedioNum = Number(metricas.promedioGeneral || 0);

  return (
    <div className="space-y-4">
      {/* Saludo Principal y Cabecera de Familia */}
      <div className="relative overflow-hidden bg-gradient-to-br from-red-600 via-rose-600 to-red-700 rounded-3xl p-5 sm:p-6 text-white shadow-lg shadow-red-600/20">
        <div className="relative z-10 flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold tracking-widest uppercase bg-white/20 px-2 py-0.5 rounded-full backdrop-blur-xs">
                Portal Familias
              </span>
              <span className="text-[10px] text-red-100">
                {periodoActivo?.nombre || "Gestión Activa"}
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black tracking-tight leading-tight">
              {saludoHora}, {usuario?.nombre || "Estimado Padre/Madre"}
            </h2>
            <p className="text-xs text-red-100 max-w-sm leading-relaxed">
              Monitorea el avance de tus hijos, recibe recomendaciones pedagógicas y descarga su boletín oficial.
            </p>
          </div>

          <div className="w-12 h-12 rounded-2xl bg-white/15 backdrop-blur-md flex items-center justify-center text-2xl border border-white/20 shadow-inner shrink-0">
            🎓
          </div>
        </div>

        {/* Botón flotante para consultar al Asistente IA sobre rendimiento */}
        <div className="relative z-10 mt-4 pt-3 border-t border-white/20 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-red-100 text-[11px]">Asistente Escolar IA conectado</span>
          </div>
          <button
            onClick={() => setChatbotOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white text-red-700 font-bold text-xs shadow-xs hover:bg-red-50 active:scale-95 transition"
          >
            <span>🤖 Orientación de Estudio</span>
            <span>➔</span>
          </button>
        </div>

        {/* Círculos decorativos de fondo */}
        <div className="absolute -right-10 -bottom-10 w-44 h-44 bg-white/5 rounded-full pointer-events-none"></div>
        <div className="absolute right-20 -top-10 w-28 h-28 bg-white/5 rounded-full pointer-events-none"></div>
      </div>

      {/* SELECTOR MULTIHIJO (Si tiene 2 o más hijos) */}
      {estudiantes && estudiantes.length > 1 && (
        <div className="bg-white rounded-3xl border border-slate-200/90 p-3.5 shadow-2xs space-y-2">
          <div className="flex items-center justify-between px-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Tus Hijos Inscritos ({estudiantes.length})
            </span>
            <span className="text-[10px] text-slate-400">Toca para cambiar</span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {estudiantes.map((est) => {
              const seleccionado = est.id === estudianteId;
              return (
                <button
                  key={est.id}
                  onClick={() => seleccionarEstudiante(est.id)}
                  className={`p-3 rounded-2xl text-left border transition-all ${
                    seleccionado
                      ? "bg-red-50/80 border-red-500 ring-2 ring-red-500/20 shadow-xs"
                      : "bg-slate-50 hover:bg-slate-100 border-slate-200"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm shrink-0 ${
                        seleccionado
                          ? "bg-red-600 text-white shadow-2xs"
                          : "bg-slate-200 text-slate-700"
                      }`}
                    >
                      {(est.nombres || "E").charAt(0)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-xs font-bold text-slate-900 truncate">
                        {est.nombres} {est.primer_apellido}
                      </div>
                      <div className="text-[10px] text-slate-500 truncate">
                        {est.grado || "Curso"}
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Ficha Principal del Hijo Activo con Medidor de Rendimiento */}
      <div className="bg-white rounded-3xl border border-slate-200/90 p-5 shadow-2xs space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-3.5">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-red-600 to-rose-500 text-white flex items-center justify-center text-2xl font-black shadow-md shadow-red-500/20">
              {(estudianteActivo.nombres || "E").charAt(0)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-black text-slate-900 text-base sm:text-lg leading-tight">
                  {estudianteActivo.nombres} {estudianteActivo.primer_apellido} {estudianteActivo.segundo_apellido || ""}
                </h3>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {estudianteActivo.grado || boletin?.curso?.nombre || "Estudiante regular"}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <span className="font-mono text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md font-semibold">
                  RUDE: {estudianteActivo.rude || "N/A"}
                </span>
                <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  Gestión {estudianteActivo.gestion || boletin?.gestion || 2026}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Medidor de Rendimiento y Promedio */}
        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white rounded-2xl p-4 sm:p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
                Promedio Acumulado
              </span>
              <div className="flex items-baseline gap-2">
                <span
                  className={`text-3xl sm:text-4xl font-black ${
                    promedioNum >= 51 ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {boletinLoading ? "..." : metricas.promedioGeneral}
                </span>
                <span className="text-xs text-slate-400">/ 100 puntos</span>
              </div>
              <span
                className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full inline-block ${
                  promedioNum >= 70
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : promedioNum >= 51
                    ? "bg-sky-500/20 text-sky-300 border border-sky-500/30"
                    : "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                }`}
              >
                {promedioNum >= 70
                  ? "Rendimiento Sobresaliente"
                  : promedioNum >= 51
                  ? "Condición: Aprobado (Promovido)"
                  : "Atención: En riesgo de reprobación"}
              </span>
            </div>

            <button
              onClick={() => descargarBoletin("docx")}
              disabled={downloading || boletinLoading}
              className="flex flex-col items-center justify-center p-3 rounded-2xl bg-white/10 hover:bg-white/20 text-white border border-white/20 transition active:scale-95 text-center"
              title="Descargar boletín oficial"
            >
              <span className="text-xl">📄</span>
              <span className="text-[10px] font-bold mt-1">
                {downloading ? "Descargando..." : "Boletín"}
              </span>
            </button>
          </div>

          {/* Barra de estado con escala mínima de aprobación */}
          <div className="mt-4 space-y-1">
            <div className="w-full h-2.5 bg-slate-700/80 rounded-full overflow-hidden relative">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  promedioNum >= 51
                    ? "bg-gradient-to-r from-emerald-500 to-teal-400"
                    : "bg-gradient-to-r from-rose-500 to-red-500"
                }`}
                style={{ width: `${Math.min(Math.max(promedioNum, 0), 100)}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>0 pts</span>
              <span className="text-amber-400 font-bold">Mínimo para aprobar: 51 pts</span>
              <span>100 pts</span>
            </div>
          </div>
        </div>

        {/* 4 Métricas Clave en Cuadrícula */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1">
          {/* Materias Aprobadas */}
          <div className="bg-slate-50 p-3 rounded-2xl border border-slate-200/80">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              Aprobadas
            </span>
            <div className="flex items-baseline gap-1 mt-1">
              <span className="text-xl font-black text-emerald-600">
                {metricas.materiasAprobadas}
              </span>
              <span className="text-xs text-slate-400">/ {metricas.totalMaterias}</span>
            </div>
            <span className="text-[10px] text-slate-500 block mt-0.5">materias</span>
          </div>

          {/* Materias en Riesgo */}
          <div className="bg-slate-50 p-3 rounded-2xl border border-slate-200/80">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              En Riesgo (&lt;51)
            </span>
            <div className="flex items-baseline gap-1 mt-1">
              <span
                className={`text-xl font-black ${
                  metricas.materiasReprobadas > 0 ? "text-rose-600" : "text-slate-700"
                }`}
              >
                {metricas.materiasReprobadas}
              </span>
              <span className="text-xs text-slate-400">materias</span>
            </div>
            <span
              className={`text-[10px] font-semibold block mt-0.5 ${
                metricas.materiasReprobadas > 0 ? "text-rose-600" : "text-emerald-600"
              }`}
            >
              {metricas.materiasReprobadas > 0 ? "Requiere apoyo" : "Sin reprobadas"}
            </span>
          </div>

          {/* Asistencia */}
          <div className="bg-slate-50 p-3 rounded-2xl border border-slate-200/80">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              Asistencia
            </span>
            <div className="flex items-baseline gap-1 mt-1">
              <span className="text-xl font-black text-sky-600">
                {metricas.asistenciaPorcentaje}%
              </span>
            </div>
            <span className="text-[10px] text-slate-500 block mt-0.5">presencia regular</span>
          </div>

          {/* Periodo de Cierre */}
          <div className="bg-slate-50 p-3 rounded-2xl border border-slate-200/80">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              Periodo
            </span>
            <div className="mt-1 font-bold text-xs text-slate-800 truncate">
              {periodoActivo?.nombre || "Trimestral"}
            </div>
            <span className="text-[10px] text-emerald-600 font-semibold block mt-0.5">En curso</span>
          </div>
        </div>
      </div>

      {/* 🧠 MÓDULO ESTRELLA: Diagnóstico y Recomendaciones IA para el Hogar */}
      <div className="bg-gradient-to-br from-red-50 via-rose-50/50 to-amber-50/40 rounded-3xl border border-red-200/90 p-5 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-red-600 text-white flex items-center justify-center text-base shadow-xs">
              🧠
            </div>
            <div>
              <h4 className="font-black text-sm text-red-950 leading-tight">
                Diagnóstico del Rendimiento Escolar (IA)
              </h4>
              <p className="text-[11px] text-slate-600 mt-0.5">
                Orientación pedagógica para el hogar sobre {estudianteActivo.nombres}
              </p>
            </div>
          </div>
          <span className="text-[10px] font-bold bg-red-200/60 text-red-900 px-2 py-0.5 rounded-full">
            Recomendaciones
          </span>
        </div>

        {/* Diagnóstico contextual automático */}
        {materiasEnRiesgo.length > 0 ? (
          <div className="bg-white rounded-2xl p-4 border border-rose-200 space-y-2.5 text-xs text-slate-700 shadow-2xs">
            <div className="flex items-center gap-2 font-bold text-rose-800 text-xs">
              <span>🚨</span>
              <span>Atención Pedagógica Requerida:</span>
            </div>
            <p className="leading-relaxed">
              {estudianteActivo.nombres} registra puntajes por debajo de los 51 puntos en:{" "}
              <strong>{materiasEnRiesgo.map((m) => `${m.area} (${m.promedio_final} pts)`).join(", ")}</strong>.
            </p>
            <div className="bg-rose-50 p-2.5 rounded-xl border border-rose-100 text-[11px] text-rose-950 space-y-1">
              <strong>💡 Consejo pedagógico para el hogar:</strong>
              <p>
                Establece una rutina de estudio fija de 25 minutos al día sin pantallas distractores para repasar los temas de estas materias. Te sugerimos solicitar una cita de orientación con sus docentes en secretaría.
              </p>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-2xl p-4 border border-emerald-200 space-y-2 text-xs text-slate-700 shadow-2xs">
            <div className="flex items-center gap-2 font-bold text-emerald-800 text-xs">
              <span>🌟</span>
              <span>Rendimiento Favorable:</span>
            </div>
            <p className="leading-relaxed">
              ¡Felicitaciones! {estudianteActivo.nombres} mantiene todas sus materias aprobadas con un promedio general de <strong>{metricas.promedioGeneral} pts</strong>.
            </p>
            {materiasDestacadas.length > 0 && (
              <p className="text-[11px] text-slate-600">
                Su mayor fortaleza académica se encuentra en: <strong>{materiasDestacadas[0].area}</strong> ({materiasDestacadas[0].promedio_final} pts).
              </p>
            )}
          </div>
        )}

        {/* Botón para interactuar con el Agente IA */}
        <button
          onClick={() => setChatbotOpen(true)}
          className="w-full py-2.5 bg-red-600 hover:bg-red-700 text-white font-bold rounded-2xl text-xs shadow-md shadow-red-600/20 transition flex items-center justify-center gap-2 active:scale-98"
        >
          <span>🤖 Pedir Consejo Personalizado al Asistente IA</span>
          <span>➔</span>
        </button>
      </div>

      {/* Vista Rápida de Asignaturas */}
      <div className="bg-white rounded-3xl border border-slate-200/90 p-5 shadow-2xs space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-bold text-sm text-slate-900">Materias Evaluadas</h4>
            <p className="text-xs text-slate-500">Resumen de asignaturas y avance de notas</p>
          </div>
          <Link
            to="/padres/calificaciones"
            className="text-xs font-bold text-red-600 hover:text-red-700 flex items-center gap-1"
          >
            <span>Ver Todo</span>
            <span>➔</span>
          </Link>
        </div>

        {boletin?.materias && boletin.materias.length > 0 ? (
          <div className="space-y-2 pt-1">
            {boletin.materias.slice(0, 4).map((m, idx) => {
              const nota = m.promedio_final != null ? Number(m.promedio_final) : null;
              const aprobada = nota != null && nota >= 51;
              return (
                <div
                  key={idx}
                  className="bg-slate-50 border border-slate-200/80 rounded-2xl p-3 flex items-center justify-between gap-3 text-xs"
                >
                  <div className="min-w-0 flex-1">
                    <span className="font-bold text-slate-800 block truncate">{m.area}</span>
                    <span className="text-[10px] text-slate-400 block truncate">
                      {m.docente || "Docente asignado"}
                    </span>
                  </div>

                  <div className="text-right shrink-0">
                    <span
                      className={`font-black text-sm block ${
                        nota != null
                          ? aprobada
                            ? "text-emerald-600"
                            : "text-rose-600"
                          : "text-slate-400"
                      }`}
                    >
                      {nota != null ? `${nota} pts` : "Sin nota"}
                    </span>
                    <span
                      className={`text-[9px] font-bold px-1.5 py-0.2 rounded ${
                        aprobada
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-rose-100 text-rose-800"
                      }`}
                    >
                      {aprobada ? "Aprobado" : "En riesgo"}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-slate-400 italic py-2 text-center">
            Notas en proceso de consolidación trimestral.
          </p>
        )}
      </div>

      {/* Accesos Directos del Portal */}
      <div className="grid grid-cols-2 gap-2.5">
        <Link
          to="/padres/calificaciones"
          className="p-4 rounded-3xl bg-white hover:bg-slate-50 border border-slate-200/90 shadow-2xs flex flex-col justify-between transition group"
        >
          <div className="w-10 h-10 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center text-xl font-bold group-hover:scale-105 transition-transform">
            📊
          </div>
          <div className="mt-3">
            <span className="font-bold text-slate-900 text-xs sm:text-sm block leading-tight">
              Boletín Completo
            </span>
            <span className="text-[10px] text-slate-500 block mt-0.5">Notas por trimestre</span>
          </div>
        </Link>

        <Link
          to="/padres/asistencia"
          className="p-4 rounded-3xl bg-white hover:bg-slate-50 border border-slate-200/90 shadow-2xs flex flex-col justify-between transition group"
        >
          <div className="w-10 h-10 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center text-xl font-bold group-hover:scale-105 transition-transform">
            📅
          </div>
          <div className="mt-3">
            <span className="font-bold text-slate-900 text-xs sm:text-sm block leading-tight">
              Asistencia y Faltas
            </span>
            <span className="text-[10px] text-slate-500 block mt-0.5">Control de clases</span>
          </div>
        </Link>
      </div>

      {/* Valores y Compromiso Fe y Alegría */}
      <div className="rounded-3xl border border-slate-200/80 bg-white p-4 shadow-2xs text-xs text-slate-500 space-y-1.5 text-center">
        <div className="font-bold text-slate-800 flex items-center justify-center gap-1.5">
          <span>❤️</span>
          <span>Unidad Educativa Divino Corazón de Jesús</span>
        </div>
        <p className="text-[11px] leading-relaxed max-w-sm mx-auto text-slate-500">
          "Donde termina el asfalto, donde no llega el agua, allí comienza Divino Corazón de Jesús para brindar una educación integral a nuestras familias."
        </p>
      </div>
    </div>
  );
}
