/**
 * Servicio de Asistente Académico para el Portal de Padres — U.E. Fe y Alegría
 *
 * ARQUITECTURA (segura):
 *   Frontend → POST /api/padres/asistente/ (backend Django, autenticado por cookie)
 *            → Backend → Groq Tool Calling → BD real
 *
 * El frontend NUNCA envía la API Key ni IDs de estudiantes.
 * El backend valida que el usuario sea un tutor y solo accede a sus propios hijos.
 *
 * Guardrail doble:
 *   1. Filtro local en JS (respuesta instantánea para casos obvios como "1+1")
 *   2. System Prompt estricto + guardrail en el backend (Groq)
 */

import { consultarAsistente } from "./padresService";

export const GROQ_MODEL = "openai/gpt-oss-120b"; // modelo real disponible en esta cuenta Groq
export const GROQ_API_URL = null; // No se usa: el frontend NO llama a Groq directamente

// ---------------------------------------------------------------------------
// Guardrail local — rechazo instantáneo sin llamada al backend
// ---------------------------------------------------------------------------
const OUT_OF_SCOPE_PATTERNS = [
  /\b\d+\s*[\+\-\*\/\^x÷]\s*\d+/,                                            // 1+1, 5*3
  /\b(cuanto|cuánto)\s+(es|son)\s+\d+/i,
  /\b(calcula|calculame|calculá|resuelve|resolver)\b/i,
  /\b(quien|quién)\s+(fue|es|descubrio|inventó?)\b/i,
  /\b(capital\s+de|receta\s+de|poema|chiste|cuento)\b/i,
  /\b(javascript|python|html|css|sql|react|codigo|código|programacion)\b/i,
  /\b(futbol|fútbol|messi|ronaldo|partido\s+de|pelicula|película)\b/i,
  /\b(clima\s+en|temperatura\s+en|dolar|bitcoin)\b/i,
];
const EXACT_BLOCKS = ["1+1", "2+2", "dime un chiste", "hazme una tarea", "escribe un ensayo"];

export function esConsultaFueraDeAlcance(pregunta) {
  if (!pregunta || typeof pregunta !== "string") return false;
  const texto = pregunta.trim().toLowerCase();
  if (EXACT_BLOCKS.some((b) => texto.includes(b))) return true;
  return OUT_OF_SCOPE_PATTERNS.some((r) => r.test(texto));
}

export function mensajeFueraDeAlcance() {
  return "Solo puedo ayudarte con el rendimiento académico de tus hijos en la U.E. Fe y Alegría.";
}

// Mantener compatibilidad con código antiguo que importaba estas funciones
export { esConsultaFueraDeAlcance as esConsultaFueraDeAlcanceLocal };

// ---------------------------------------------------------------------------
// Helpers de retrocompatibilidad (ya no se usan internamente)
// ---------------------------------------------------------------------------
export function getGroqApiKey() {
  // La API Key solo existe en el backend (.env del servidor).
  // Esta función retorna vacío deliberadamente para evitar exposición.
  return "";
}
export function hasGroqKey() {
  // El frontend siempre considera que el asistente está disponible
  // (el backend manejará el error si la clave no está configurada).
  return true;
}
export const getGeminiApiKey = getGroqApiKey;
export const hasGeminiKey = hasGroqKey;

// ---------------------------------------------------------------------------
// Función principal del asistente
// ---------------------------------------------------------------------------
/**
 * Consulta al Asistente Académico de Fe y Alegría.
 *
 * @param {string} pregunta   - Texto del tutor
 * @param {object} _contexto  - (ignorado — el backend obtiene datos de la sesión)
 * @param {Array}  historial  - [{sender: "user"|"bot", text: string}]
 *
 * @returns {Promise<{tipo, respuesta, fuente, modelo?}>}
 */
export async function consultarAgenteIA(pregunta, _contexto = null, historial = []) {
  const q = (pregunta || "").trim();

  // 1. Guardrail local inmediato (sin llamada de red)
  if (esConsultaFueraDeAlcance(q)) {
    return {
      tipo: "fuera_de_alcance",
      respuesta: mensajeFueraDeAlcance(),
      fuente: "guardrail_local",
    };
  }

  // 2. Llamar al backend seguro
  try {
    const resultado = await consultarAsistente(q, historial);
    return {
      tipo: resultado.fuente === "guardrail" ? "fuera_de_alcance" : "ia_generativa",
      respuesta: resultado.respuesta || "No pude generar una respuesta.",
      fuente: resultado.fuente || "backend",
      modelo: resultado.modelo || GROQ_MODEL,
    };
  } catch (error) {
    // Si el backend devuelve 403 (no es tutor) o 401 (no autenticado)
    const status = error?.response?.status;
    if (status === 403) {
      return {
        tipo: "error",
        respuesta: "No tienes permisos para usar el asistente académico.",
        fuente: "error_403",
      };
    }
    if (status === 401) {
      return {
        tipo: "error",
        respuesta: "Tu sesión ha expirado. Por favor, vuelve a iniciar sesión.",
        fuente: "error_401",
      };
    }
    console.error("Error al contactar el asistente académico:", error);
    return {
      tipo: "error",
      respuesta: "El asistente no está disponible en este momento. Por favor, intenta de nuevo.",
      fuente: "error_red",
    };
  }
}
