import React, { useState, useEffect, useRef } from "react";
import { usePadres } from "../../context/PadresContext";
import {
  consultarAgenteIA,
  hasGroqKey,
  GROQ_MODEL,
} from "../../services/groqAiService";

export default function ChatbotModal() {
  const {
    chatbotOpen,
    setChatbotOpen,
    usuario,
    estudiantes,
    estudianteActivo,
    seleccionarEstudiante,
    todosBoletines,
    descargarBoletin,
  } = usePadres();

  const [inputTexto, setInputTexto] = useState("");
  const [typing, setTyping] = useState(false);
  const [mensajes, setMensajes] = useState([]);
  const chatEndRef = useRef(null);

  const usaGroq = hasGroqKey();

  // Inicializar mensajes de bienvenida al abrir el modal
  useEffect(() => {
    if (chatbotOpen && mensajes.length === 0) {
      const nombreHijos = (estudiantes || []).map((e) => e.nombres).join(" y ");
      setMensajes([
        {
          id: "init-1",
          sender: "bot",
          text: `¡Hola, estimado(a) **${usuario?.nombre || "Tutor"}**! 👋 Soy tu Asistente Escolar y Pedagógico de U.E. Divino Corazón de Jesús.`,
          tiempo: "Ahora",
        },
        {
          id: "init-2",
          sender: "bot",
          text:
            estudiantes && estudiantes.length > 1
              ? `Tengo acceso a la información académica de tus **${estudiantes.length} hijos**: **${nombreHijos}**. Puedo ayudarte a analizar sus notas, sugerir rutinas de estudio en casa, identificar materias en riesgo (<51 pts) o comparar su progreso.`
              : `Tengo acceso al registro académico de tu hijo(a) **${estudianteActivo?.nombres || "estudiante"}**. Puedo ayudarte con consejos de estudio, análisis de materias en riesgo (<51 pts), asistencia y recomendaciones docentes.`,
          tiempo: "Ahora",
          sugerencias:
            estudiantes && estudiantes.length > 1
              ? [
                  "¿Cómo van mis hijos?",
                  "¿Quién tiene materias en riesgo (<51)?",
                  "Consejos para mejorar el rendimiento escolar",
                  "Asistencia y faltas de ambos",
                ]
              : [
                  "¿Tiene materias en riesgo (<51)?",
                  "¿Cómo puedo ayudarle a mejorar su promedio?",
                  "¿Cuál es su promedio general?",
                  "Observaciones de profesores",
                  "Descargar boletín oficial",
                ],
        },
      ]);
    }
  }, [chatbotOpen, estudiantes, estudianteActivo, usuario, mensajes.length]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajes, typing]);

  if (!chatbotOpen) return null;

  const handleEnviarMensaje = async (textoPersonalizado = null) => {
    const texto = (textoPersonalizado || inputTexto).trim();
    if (!texto) return;

    const nuevoMsgUser = {
      id: `u-${Date.now()}`,
      sender: "user",
      text: texto,
      tiempo: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMensajes((prev) => [...prev, nuevoMsgUser]);
    if (!textoPersonalizado) setInputTexto("");
    setTyping(true);

    const contexto = {
      tutor: usuario,
      estudiantes,
      estudianteActivo,
      todosBoletines,
    };

    try {
      const resultado = await consultarAgenteIA(texto, contexto, mensajes);
      setTyping(false);

      const nuevoMsgBot = {
        id: `b-${Date.now()}`,
        sender: "bot",
        text: resultado.respuesta,
        tipo: resultado.tipo,
        fuente: resultado.fuente,
        tiempo: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        accionDescarga: resultado.tipo === "descarga",
      };

      setMensajes((prev) => [...prev, nuevoMsgBot]);
    } catch (_err) {
      setTyping(false);
      setMensajes((prev) => [
        ...prev,
        {
          id: `b-${Date.now()}`,
          sender: "bot",
          text: "Ocurrió un inconveniente temporal al procesar tu solicitud. Por favor, reintenta en unos instantes.",
          tiempo: "Ahora",
        },
      ]);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-sm p-0 sm:p-4 transition-all">
      <div
        className="w-full sm:max-w-xl bg-white rounded-t-3xl sm:rounded-2xl shadow-2xl flex flex-col h-[92vh] sm:h-[84vh] max-h-[850px] overflow-hidden animate-in slide-in-from-bottom duration-200"
        role="dialog"
        aria-modal="true"
      >
        {/* Cabecera del Asistente */}
        <div className="bg-gradient-to-r from-red-600 to-rose-700 text-white p-3.5 sm:p-4 flex items-center justify-between shrink-0 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-10 h-10 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center text-xl shadow-inner border border-white/20">
                🤖
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 border-2 border-red-600 rounded-full"></span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-sm sm:text-base leading-tight">
                  Agente Pedagógico IA
                </h3>
                {usaGroq ? (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-400 text-slate-950 flex items-center gap-1 shadow-2xs">
                    <span>🚀</span>
                    <span>Groq (Tool Calling)</span>
                  </span>
                ) : (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-400 text-slate-950 flex items-center gap-1 shadow-2xs">
                    <span>⚡</span>
                    <span>IA Local</span>
                  </span>
                )}
              </div>
              <p className="text-[11px] text-rose-100 mt-0.5">
                U.E. Divino Corazón de Jesús • Orientación a Familias
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setChatbotOpen(false)}
              className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition text-base"
              aria-label="Cerrar asistente"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Selector rápido de hijo en el chat si tiene varios */}
        {estudiantes && estudiantes.length > 1 && (
          <div className="bg-slate-100 border-b border-slate-200 px-3.5 py-2 flex items-center gap-2 text-xs overflow-x-auto scrollbar-none shrink-0">
            <span className="text-[10px] uppercase font-bold text-slate-400 shrink-0">
              Enfoque:
            </span>
            {estudiantes.map((est) => {
              const activo = est.id === estudianteActivo?.id;
              return (
                <button
                  key={est.id}
                  onClick={() => seleccionarEstudiante(est.id)}
                  className={`px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition border ${
                    activo
                      ? "bg-red-600 text-white border-red-600 shadow-2xs"
                      : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                  }`}
                >
                  {est.nombres} ({est.grado || "Curso"})
                </button>
              );
            })}
          </div>
        )}

        {/* Cuerpo de la Conversación */}
        <div className="p-3.5 sm:p-4 overflow-y-auto space-y-3.5 bg-slate-50/70 flex-1 text-xs sm:text-sm">
          {mensajes.map((m) => (
            <div
              key={m.id}
              className={`flex flex-col ${
                m.sender === "user" ? "items-end" : "items-start"
              }`}
            >
              <div
                className={`max-w-[88%] rounded-2xl p-3.5 shadow-2xs leading-relaxed ${
                  m.sender === "user"
                    ? "bg-red-600 text-white rounded-br-xs"
                    : "bg-white text-slate-800 border border-slate-200/90 rounded-bl-xs"
                }`}
              >
                <div className="whitespace-pre-wrap">{m.text}</div>

                {/* Badge de fuente si es Groq */}
                {(m.fuente === "groq" || m.fuente === "groq_tool" || m.fuente === "groq_directo") && (
                  <div className="mt-2 text-[9px] text-slate-400 flex items-center gap-1 border-t border-slate-100 pt-1">
                    <span>🚀</span>
                    <span>Respuesta generada por Groq {m.fuente === "groq_tool" ? "(Tool Calling)" : ""}</span>
                  </div>
                )}

                {/* Botón de acción para descarga si aplica */}
                {m.accionDescarga && (
                  <div className="mt-3 pt-2.5 border-t border-slate-100">
                    <button
                      onClick={() => descargarBoletin("docx")}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl text-xs shadow-xs transition"
                    >
                      <span>📥 Descargar Boletín Oficial (Word)</span>
                    </button>
                  </div>
                )}
              </div>

              <span className="text-[9px] text-slate-400 mt-1 px-1">
                {m.tiempo}
              </span>

              {/* Sugerencias de preguntas rápidas */}
              {m.sugerencias && m.sugerencias.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2 max-w-[95%]">
                  {m.sugerencias.map((sug, sIdx) => (
                    <button
                      key={sIdx}
                      onClick={() => handleEnviarMensaje(sug)}
                      className="text-[11px] font-semibold bg-white hover:bg-red-50 text-red-700 border border-red-200 rounded-full px-3 py-1 shadow-2xs transition active:scale-95 text-left"
                    >
                      {sug}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}

          {/* Animación "Escribiendo" */}
          {typing && (
            <div className="flex items-center gap-1.5 bg-white p-2.5 px-4 rounded-2xl rounded-bl-xs border border-slate-200 w-fit text-slate-400 shadow-2xs">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-bounce"></span>
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-bounce delay-100"></span>
              <span className="w-1.5 h-1.5 rounded-full bg-red-600 animate-bounce delay-200"></span>
              <span className="text-[11px] text-slate-500 ml-1">Analizando rendimiento...</span>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Barra de Entrada de Consultas */}
        <div className="p-3 bg-white border-t border-slate-200 shrink-0">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleEnviarMensaje();
            }}
            className="flex gap-2"
          >
            <input
              type="text"
              value={inputTexto}
              onChange={(e) => setInputTexto(e.target.value)}
              placeholder="Pregunta sobre notas, consejos de estudio, materias en riesgo..."
              className="flex-1 bg-slate-100 border border-slate-300 rounded-2xl px-4 py-2.5 text-xs sm:text-sm focus:outline-none focus:border-red-500 focus:bg-white transition"
              autoFocus
            />
            <button
              type="submit"
              disabled={!inputTexto.trim() || typing}
              className="w-10 h-10 rounded-2xl bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white flex items-center justify-center font-bold text-sm shadow-sm transition shrink-0 active:scale-95"
              title="Enviar consulta"
            >
              ➔
            </button>
          </form>

          {/* Nota de delimitación del agente */}
          <div className="flex items-center justify-between text-[10px] text-slate-400 mt-1.5 px-1">
            <span>🔒 Agente orientado exclusivamente al desempeño de tus hijos.</span>
            <span>U.E. Divino Corazón de Jesús</span>
          </div>
        </div>
      </div>
    </div>
  );
}
