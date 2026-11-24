import React, { useState, useMemo } from "react";
import { usePadres } from "../../context/PadresContext";

export default function PadresCalificacionesPage() {
  const {
    estudianteActivo,
    boletin,
    boletinLoading,
    boletinError,
    recargarBoletin,
    periodoSeleccionadoId,
    setPeriodoSeleccionadoId,
    descargarBoletin,
    downloading,
  } = usePadres();

  const [filtroTexto, setFiltroTexto] = useState("");
  const [filtroEstado, setFiltroEstado] = useState("todos"); // 'todos', 'aprobadas', 'reprobadas'

  const periodos = boletin?.periodos || [];

  // Calcular estadísticas según periodo seleccionado
  const materiasProcesadas = useMemo(() => {
    if (!boletin?.materias) return [];

    return boletin.materias.map((m) => {
      let notaActual = null;
      if (periodoSeleccionadoId === "todos") {
        notaActual = m.promedio_final != null ? Number(m.promedio_final) : null;
      } else {
        const val = m.notas_por_periodo?.[periodoSeleccionadoId];
        notaActual = val != null ? Number(val) : null;
      }

      // Buscar observación para esta materia y periodo
      const obsMateria = (boletin.observaciones || []).filter(
        (o) =>
          o.area?.toLowerCase() === m.area?.toLowerCase() &&
          (periodoSeleccionadoId === "todos" || String(o.periodo_id) === String(periodoSeleccionadoId))
      );

      return {
        ...m,
        notaActual,
        aprobada: notaActual != null ? notaActual >= 51 : null,
        observaciones: obsMateria,
      };
    });
  }, [boletin, periodoSeleccionadoId]);

  // Filtrado por texto y estado
  const materiasFiltradas = useMemo(() => {
    return materiasProcesadas.filter((m) => {
      const coincideTexto =
        !filtroTexto.trim() ||
        m.area.toLowerCase().includes(filtroTexto.toLowerCase()) ||
        (m.docente && m.docente.toLowerCase().includes(filtroTexto.toLowerCase()));

      if (!coincideTexto) return false;

      if (filtroEstado === "aprobadas") {
        return m.aprobada === true;
      }
      if (filtroEstado === "reprobadas") {
        return m.aprobada === false;
      }
      return true;
    });
  }, [materiasProcesadas, filtroTexto, filtroEstado]);

  // Promedio y conteos del periodo actual seleccionado
  const estadisticasPeriodo = useMemo(() => {
    let suma = 0;
    let conNota = 0;
    let aprobadas = 0;
    let reprobadas = 0;

    materiasProcesadas.forEach((m) => {
      if (m.notaActual != null) {
        suma += m.notaActual;
        conNota += 1;
        if (m.notaActual >= 51) {
          aprobadas += 1;
        } else {
          reprobadas += 1;
        }
      }
    });

    const promedio = conNota > 0 ? (suma / conNota).toFixed(1) : "0";
    return { promedio, conNota, aprobadas, reprobadas, total: materiasProcesadas.length };
  }, [materiasProcesadas]);

  if (boletinLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-500 gap-3">
        <div className="w-10 h-10 border-4 border-red-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-medium">Cargando calificaciones oficiales...</p>
      </div>
    );
  }

  if (boletinError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-2xl p-5 text-red-700 text-sm space-y-3">
        <div className="font-bold flex items-center gap-2">
          <span>⚠️</span>
          <span>Error al consultar notas</span>
        </div>
        <p>{boletinError}</p>
        <button
          onClick={recargarBoletin}
          className="px-4 py-2 bg-red-600 text-white rounded-xl text-xs font-semibold hover:bg-red-700 transition"
        >
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Selector de Periodo / Trimestre */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-2 shadow-2xs">
        <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          <button
            onClick={() => setPeriodoSeleccionadoId("todos")}
            className={`px-3 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition ${
              periodoSeleccionadoId === "todos"
                ? "bg-red-600 text-white shadow-xs"
                : "bg-slate-50 text-slate-600 hover:bg-slate-100"
            }`}
          >
            Promedio Anual
          </button>
          {periodos.map((p) => {
            const isSel = String(p.id) === String(periodoSeleccionadoId);
            return (
              <button
                key={p.id}
                onClick={() => setPeriodoSeleccionadoId(String(p.id))}
                className={`px-3 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition ${
                  isSel
                    ? "bg-red-600 text-white shadow-xs"
                    : "bg-slate-50 text-slate-600 hover:bg-slate-100"
                }`}
              >
                {p.nombre}
              </button>
            );
          })}
        </div>
      </div>

      {/* Resumen del periodo seleccionado */}
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-2xl p-4 sm:p-5 shadow-md">
        <div className="flex items-center justify-between pb-3 border-b border-slate-700">
          <div>
            <span className="text-[10px] uppercase tracking-wider font-bold text-slate-400">
              {periodoSeleccionadoId === "todos"
                ? "Calificación General de Gestión"
                : periodos.find((p) => String(p.id) === String(periodoSeleccionadoId))?.nombre || "Trimestre"}
            </span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="text-3xl font-black text-white">
                {estadisticasPeriodo.promedio}
              </span>
              <span className="text-xs text-slate-400">/ 100 pts</span>
              <span
                className={`ml-2 text-xs font-bold px-2.5 py-0.5 rounded-full ${
                  Number(estadisticasPeriodo.promedio) >= 51
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                    : "bg-red-500/20 text-red-400 border border-red-500/30"
                }`}
              >
                {Number(estadisticasPeriodo.promedio) >= 51 ? "Aprobado" : "Reprobado"}
              </span>
            </div>
          </div>

          <button
            onClick={() => descargarBoletin("docx")}
            disabled={downloading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-red-600 hover:bg-red-700 active:scale-95 text-white text-xs font-bold transition shadow-sm"
            title="Descargar boletín oficial en formato Word"
          >
            <span>{downloading ? "Descargando..." : "Descargar"}</span>
            <span>📄</span>
          </button>
        </div>

        <div className="grid grid-cols-3 gap-2 pt-3 text-center text-xs">
          <div>
            <span className="text-[10px] text-slate-400 block">Evaluadas</span>
            <span className="font-bold text-white text-base">
              {estadisticasPeriodo.conNota} / {estadisticasPeriodo.total}
            </span>
          </div>
          <div>
            <span className="text-[10px] text-emerald-400 block">Aprobadas</span>
            <span className="font-bold text-emerald-400 text-base">
              {estadisticasPeriodo.aprobadas}
            </span>
          </div>
          <div>
            <span className="text-[10px] text-red-400 block">En Riesgo</span>
            <span className="font-bold text-red-400 text-base">
              {estadisticasPeriodo.reprobadas}
            </span>
          </div>
        </div>
      </div>

      {/* Buscador y Filtros */}
      <div className="space-y-2">
        <div className="relative">
          <input
            type="text"
            value={filtroTexto}
            onChange={(e) => setFiltroTexto(e.target.value)}
            placeholder="Buscar materia o docente..."
            className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 pl-9 text-xs sm:text-sm text-slate-800 focus:outline-none focus:border-red-500 transition shadow-2xs"
          />
          <span className="absolute left-3 top-3 text-slate-400 text-xs">🔍</span>
          {filtroTexto && (
            <button
              onClick={() => setFiltroTexto("")}
              className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 text-xs w-5 h-5 rounded-full bg-slate-100 flex items-center justify-center"
            >
              ✕
            </button>
          )}
        </div>

        {/* Filtros de estado */}
        <div className="flex gap-2">
          <button
            onClick={() => setFiltroEstado("todos")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
              filtroEstado === "todos"
                ? "bg-slate-800 text-white border-slate-800"
                : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
            }`}
          >
            Todas ({materiasProcesadas.length})
          </button>
          <button
            onClick={() => setFiltroEstado("aprobadas")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
              filtroEstado === "aprobadas"
                ? "bg-emerald-600 text-white border-emerald-600"
                : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
            }`}
          >
            Aprobadas (≥51)
          </button>
          <button
            onClick={() => setFiltroEstado("reprobadas")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
              filtroEstado === "reprobadas"
                ? "bg-red-600 text-white border-red-600"
                : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
            }`}
          >
            En Riesgo (&lt;51)
          </button>
        </div>
      </div>

      {/* Listado de Materias */}
      {materiasFiltradas.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-slate-500 space-y-2">
          <div className="text-2xl">📋</div>
          <p className="text-sm font-medium">No se encontraron materias con los filtros seleccionados.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {materiasFiltradas.map((materia, idx) => {
            const nota = materia.notaActual;
            const tieneNota = nota != null;
            const aprobada = tieneNota && nota >= 51;
            const progresoPorcentaje = tieneNota ? Math.min(Math.max(nota, 0), 100) : 0;

            return (
              <div
                key={materia.area_id || idx}
                className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-2xs hover:shadow-xs transition space-y-3"
              >
                {/* Header de la materia */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <h4 className="font-bold text-slate-900 text-sm sm:text-base leading-snug">
                      {materia.area}
                    </h4>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Docente: {materia.docente || "No asignado"}
                    </p>
                  </div>

                  {/* Nota destacada */}
                  <div className="text-right shrink-0">
                    {tieneNota ? (
                      <div className="flex flex-col items-end">
                        <span
                          className={`text-2xl font-black leading-none ${
                            aprobada ? "text-emerald-600" : "text-red-600"
                          }`}
                        >
                          {nota}
                        </span>
                        <span
                          className={`mt-1 text-[10px] font-bold px-2 py-0.5 rounded-md ${
                            aprobada
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : "bg-red-50 text-red-700 border border-red-200"
                          }`}
                        >
                          {aprobada ? "APROBADO" : "REPROBADO"}
                        </span>
                      </div>
                    ) : (
                      <span className="text-xs font-semibold text-slate-400 bg-slate-100 px-2 py-1 rounded-md">
                        Pendiente
                      </span>
                    )}
                  </div>
                </div>

                {/* Barra de progreso visual (0 a 100 pts con marca en 51 pts) */}
                <div className="space-y-1">
                  <div className="relative w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    {/* Barra de nota */}
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        aprobada
                          ? "bg-gradient-to-r from-emerald-500 to-teal-500"
                          : "bg-gradient-to-r from-red-500 to-rose-500"
                      }`}
                      style={{ width: `${progresoPorcentaje}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-400 font-medium px-0.5">
                    <span>0 pts</span>
                    <span className="text-amber-600 font-semibold">Min: 51 pts</span>
                    <span>100 pts</span>
                  </div>
                </div>

                {/* Historial de periodos de la materia */}
                <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-[11px] font-medium text-slate-400">Trimestres:</span>
                  <div className="flex gap-1.5">
                    {periodos.map((p) => {
                      const notaPeriodo = materia.notas_por_periodo?.[p.id];
                      const tiene = notaPeriodo != null;
                      const apr = tiene && Number(notaPeriodo) >= 51;
                      return (
                        <div
                          key={p.id}
                          className={`px-2 py-1 rounded-lg text-center font-mono text-[11px] font-bold border ${
                            tiene
                              ? apr
                                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                : "bg-red-50 text-red-700 border-red-200"
                              : "bg-slate-50 text-slate-400 border-slate-200"
                          }`}
                          title={`${p.nombre}: ${tiene ? notaPeriodo : "Sin nota"}`}
                        >
                          <span className="text-[9px] block font-sans text-slate-400 font-normal">
                            {p.nombre.replace(/Trimestre/i, "T")}
                          </span>
                          {tiene ? notaPeriodo : "-"}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Observaciones pedagógicas del docente si existen */}
                {materia.observaciones && materia.observaciones.length > 0 && (
                  <div className="mt-2 bg-amber-50/70 rounded-xl p-2.5 border border-amber-200/70 text-xs text-amber-900 space-y-1">
                    {materia.observaciones.map((obs, oIdx) => (
                      <div key={oIdx} className="space-y-0.5">
                        <div className="flex items-center gap-1.5 font-bold text-amber-800 text-[11px]">
                          <span>💬 Observación docente ({obs.periodo}):</span>
                          {obs.indicador && (
                            <span className="px-1.5 py-0.2 rounded bg-amber-200 text-amber-900 text-[10px] font-mono">
                              {obs.indicador}
                            </span>
                          )}
                        </div>
                        <p className="text-amber-900/90 text-[11px] italic">
                          "{obs.observacion}"
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Escala de Aprobación Footer */}
      <div className="bg-slate-50 rounded-2xl border border-slate-200 p-3.5 text-xs text-slate-500 space-y-1.5">
        <div className="font-bold text-slate-700">Guía de Calificación Escolar:</div>
        <ul className="space-y-1 list-disc list-inside text-[11px]">
          <li><strong>51 a 100 puntos:</strong> Aprobado (Promovido).</li>
          <li><strong>1 a 50 puntos:</strong> Reprobado (Requiere apoyo y nivelación).</li>
          <li><strong>Indicadores:</strong> PA (En Desarrollo), SA (Satisfactorio), A (Avanzado), EA (Excelente).</li>
        </ul>
      </div>
    </div>
  );
}
