import React, { useState } from "react";
import { usePadres } from "../../context/PadresContext";

export default function StudentSelector() {
  const { estudiantes, estudianteId, seleccionarEstudiante, estudianteActivo } = usePadres();
  const [modalOpen, setModalOpen] = useState(false);

  if (!estudiantes || estudiantes.length === 0) {
    return null;
  }

  // Si solo hay un estudiante, mostramos tarjeta informativa
  if (estudiantes.length === 1) {
    const est = estudiantes[0];
    return (
      <div className="bg-white/95 backdrop-blur-sm border border-slate-200/80 rounded-2xl p-3 shadow-xs flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-red-600 to-rose-500 text-white flex items-center justify-center font-bold text-base shadow-sm">
            {(est.nombres || "E").charAt(0)}
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-800 leading-tight">
              {est.nombres} {est.primer_apellido}
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              {est.grado || "Estudiante regular"} {est.gestion ? `• ${est.gestion}` : ""}
            </p>
          </div>
        </div>
        <span className="text-[11px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
          Activo
        </span>
      </div>
    );
  }

  // Si hay más de un hijo: mostramos selector con modal y pills táctiles
  return (
    <>
      <div className="bg-white/95 backdrop-blur-sm border border-slate-200/80 rounded-2xl p-2.5 sm:p-3 shadow-xs">
        <div className="flex items-center justify-between mb-2 px-1">
          <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-500">
            Tus Hijos ({estudiantes.length})
          </span>
          <button
            onClick={() => setModalOpen(true)}
            className="text-xs font-semibold text-red-600 hover:text-red-700 flex items-center gap-1"
          >
            <span>Cambiar</span>
            <span>⇄</span>
          </button>
        </div>

        {/* Horizontal scrollable pills */}
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
          {estudiantes.map((est) => {
            const isSelected = est.id === estudianteId;
            return (
              <button
                key={est.id}
                onClick={() => seleccionarEstudiante(est.id)}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-left whitespace-nowrap transition-all border ${
                  isSelected
                    ? "bg-red-600 text-white border-red-600 shadow-sm shadow-red-200 font-semibold"
                    : "bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200"
                }`}
              >
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                    isSelected ? "bg-white text-red-600" : "bg-slate-200 text-slate-700"
                  }`}
                >
                  {(est.nombres || "E").charAt(0)}
                </div>
                <div>
                  <div className="text-xs leading-none">
                    {est.nombres} {est.primer_apellido}
                  </div>
                  <div
                    className={`text-[10px] leading-tight mt-0.5 ${
                      isSelected ? "text-red-100" : "text-slate-400"
                    }`}
                  >
                    {est.grado || "Sin curso"}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Modal para selección cuando hay varios */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-5 shadow-xl animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-800 text-base">Seleccionar Estudiante</h3>
              <button
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 text-lg w-7 h-7 flex items-center justify-center rounded-full hover:bg-slate-100"
              >
                ✕
              </button>
            </div>
            <div className="py-3 space-y-2 max-h-72 overflow-y-auto">
              {estudiantes.map((est) => {
                const isSelected = est.id === estudianteId;
                return (
                  <button
                    key={est.id}
                    onClick={() => {
                      seleccionarEstudiante(est.id);
                      setModalOpen(false);
                    }}
                    className={`w-full flex items-center justify-between p-3 rounded-xl border text-left transition ${
                      isSelected
                        ? "bg-red-50 border-red-300 ring-2 ring-red-500/20"
                        : "bg-white hover:bg-slate-50 border-slate-200"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-red-600 text-white font-bold flex items-center justify-center text-sm">
                        {(est.nombres || "E").charAt(0)}
                      </div>
                      <div>
                        <div className="font-semibold text-sm text-slate-800">
                          {est.nombres} {est.primer_apellido} {est.segundo_apellido || ""}
                        </div>
                        <div className="text-xs text-slate-500">
                          {est.grado || "Curso"} {est.rude ? `• RUDE: ${est.rude}` : ""}
                        </div>
                      </div>
                    </div>
                    {isSelected && (
                      <span className="w-5 h-5 rounded-full bg-red-600 text-white flex items-center justify-center text-xs">
                        ✓
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
            <button
              onClick={() => setModalOpen(false)}
              className="w-full mt-2 py-2.5 bg-slate-100 text-slate-700 font-medium rounded-xl text-sm hover:bg-slate-200 transition"
            >
              Listo
            </button>
          </div>
        </div>
      )}
    </>
  );
}
