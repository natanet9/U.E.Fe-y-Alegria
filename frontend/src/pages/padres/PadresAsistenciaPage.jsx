import React from "react";
import { usePadres } from "../../context/PadresContext";

export default function PadresAsistenciaPage() {
  const { estudianteActivo, boletin, boletinLoading, boletinError, setChatbotOpen } = usePadres();

  if (boletinLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-500 gap-3">
        <div className="w-10 h-10 border-4 border-red-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-medium">Cargando reporte de asistencia y observaciones...</p>
      </div>
    );
  }

  if (boletinError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-2xl p-5 text-red-700 text-sm">
        <div className="font-bold flex items-center gap-2 mb-1">
          <span>⚠️</span>
          <span>Error al consultar información</span>
        </div>
        <p>{boletinError}</p>
      </div>
    );
  }

  const asistencias = boletin?.asistencias || [];
  const observaciones = boletin?.observaciones || [];

  // Totales acumulados
  let totalClases = 0;
  let totalPresentes = 0;
  asistencias.forEach((a) => {
    totalClases += a.total || 0;
    totalPresentes += a.presentes || 0;
  });
  const totalFaltas = Math.max(totalClases - totalPresentes, 0);
  const porcentajeGlobal = totalClases > 0 ? Math.round((totalPresentes / totalClases) * 100) : 100;

  return (
    <div className="space-y-4">
      {/* Resumen Global de Asistencia */}
      <div className="bg-gradient-to-br from-slate-900 to-sky-950 text-white rounded-2xl p-5 shadow-md">
        <div className="flex items-center justify-between pb-3 border-b border-slate-700/80">
          <div>
            <span className="text-[10px] uppercase font-bold tracking-wider text-sky-300">
              Control de Asistencia Escolar
            </span>
            <h3 className="text-xl font-black mt-0.5">
              {estudianteActivo?.nombres} {estudianteActivo?.primer_apellido}
            </h3>
            <p className="text-xs text-slate-300 mt-0.5">
              Gestión {boletin?.gestion || new Date().getFullYear()}
            </p>
          </div>

          <div className="text-right">
            <span className="text-3xl font-black text-sky-400">
              {porcentajeGlobal}%
            </span>
            <span className="block text-[10px] text-slate-300 font-medium">Presencia regular</span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 pt-3 text-center text-xs">
          <div>
            <span className="text-[10px] text-slate-400 block">Total Clases</span>
            <span className="font-bold text-white text-base">{totalClases}</span>
          </div>
          <div>
            <span className="text-[10px] text-emerald-400 block">Asistencias</span>
            <span className="font-bold text-emerald-400 text-base">{totalPresentes}</span>
          </div>
          <div>
            <span className="text-[10px] text-rose-400 block">Inasistencias</span>
            <span className="font-bold text-rose-400 text-base">{totalFaltas}</span>
          </div>
        </div>
      </div>

      {/* Asistencia detallada por Trimestre */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-2xs space-y-3">
        <h4 className="font-bold text-slate-800 text-sm flex items-center gap-2">
          <span>📊</span>
          <span>Desglose por Periodo Trimestral</span>
        </h4>

        {asistencias.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-2 text-center">
            No se registran periodos con asistencias computadas aún.
          </p>
        ) : (
          <div className="space-y-3">
            {asistencias.map((a, idx) => {
              const faltasPeriodo = Math.max((a.total || 0) - (a.presentes || 0), 0);
              const pct = a.porcentaje != null ? Number(a.porcentaje) : 100;
              const estadoBueno = pct >= 85;

              return (
                <div
                  key={a.periodo_id || idx}
                  className="bg-slate-50 border border-slate-200 rounded-xl p-3 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs sm:text-sm text-slate-800">
                      {a.periodo}
                    </span>
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                        estadoBueno
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                          : "bg-amber-100 text-amber-800 border border-amber-200"
                      }`}
                    >
                      {pct}% Asistencia
                    </span>
                  </div>

                  {/* Barra de asistencia */}
                  <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        estadoBueno ? "bg-emerald-500" : "bg-amber-500"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>

                  <div className="flex justify-between text-[11px] text-slate-500 pt-0.5">
                    <span>Clases evaluadas: <strong>{a.total}</strong></span>
                    <span>Asistió: <strong className="text-emerald-700">{a.presentes}</strong></span>
                    <span>Faltas: <strong className="text-rose-700">{faltasPeriodo}</strong></span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Observaciones Cualitativas de los Docentes */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-2xs space-y-3">
        <h4 className="font-bold text-slate-800 text-sm flex items-center gap-2">
          <span>💬</span>
          <span>Observaciones Cualitativas y Recomendaciones</span>
        </h4>

        {observaciones.length === 0 ? (
          <div className="py-6 text-center text-slate-400 space-y-1">
            <span className="text-2xl">📝</span>
            <p className="text-xs">No hay observaciones pedagógicas registradas por los docentes todavía.</p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {observaciones.map((obs, idx) => (
              <div
                key={idx}
                className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <div className="font-bold text-slate-800 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-red-600"></span>
                    <span>{obs.area || "Área General"}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-slate-400 font-medium">
                      {obs.periodo}
                    </span>
                    {obs.indicador && (
                      <span className="bg-red-100 text-red-800 font-mono font-bold text-[10px] px-1.5 py-0.2 rounded">
                        {obs.indicador}
                      </span>
                    )}
                  </div>
                </div>

                <p className="text-slate-700 text-xs italic bg-white p-2.5 rounded-lg border border-slate-100">
                  "{obs.observacion}"
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Justificación de Licencias e Inasistencias */}
      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-amber-900 space-y-2">
        <div className="flex items-center gap-2 font-bold text-sm text-amber-900">
          <span>📋</span>
          <span>¿Cómo justificar una inasistencia?</span>
        </div>
        <p className="text-xs text-amber-800/90 leading-relaxed">
          Las faltas por motivos de salud, viaje o duelo familiar deben justificarse formalmente ante la regencia o dirección con el respaldo médico o carta correspondiente en un plazo máximo de 48 horas.
        </p>
        <button
          onClick={() => setChatbotOpen(true)}
          className="mt-1 text-xs font-bold text-amber-950 underline hover:text-black flex items-center gap-1"
        >
          <span>Consultar requisitos al Asistente IA</span>
          <span>➔</span>
        </button>
      </div>
    </div>
  );
}
