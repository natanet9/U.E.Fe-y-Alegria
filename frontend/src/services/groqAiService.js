/**
 * Servicio de Agente IA con Groq Cloud API para el Portal de Padres
 * Provee orientación pedagógica sobre rendimiento escolar, hábitos de estudio y análisis de notas
 * utilizando modelos de alta velocidad como LLaMA 3.3 (70B) o LLaMA 3.1 (8B).
 *
 * Fuente de la API Key:
 * - Estrictamente desde variable de entorno (.env): process.env.REACT_APP_GROQ_API_KEY
 */

import { esConsultaFueraDeAlcance, mensajeFueraDeAlcance, procesarConsultaPadres } from "./aiChatbotService.js";

export const GROQ_MODEL = "llama-3.3-70b-versatile";
const GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions";

/**
 * Obtiene la API Key de Groq exclusivamente de las variables de entorno (.env).
 * No permite sobreescritura desde el almacenamiento local ni la interfaz de usuario.
 */
export function getGroqApiKey() {
  const envKey = process.env.REACT_APP_GROQ_API_KEY;
  if (envKey && typeof envKey === "string" && envKey.trim()) {
    // Si viene entre comillas simples o dobles en el .env, removerlas
    return envKey.trim().replace(/^['"]|['"]$/g, "");
  }
  return "";
}

export function hasGroqKey() {
  const k = getGroqApiKey();
  return Boolean(k && k.length > 15);
}

// Aliases para retrocompatibilidad
export const getGeminiApiKey = getGroqApiKey;
export const hasGeminiKey = hasGroqKey;

/**
 * Construye el prompt de sistema enriquecido con los datos académicos de los hijos del tutor.
 */
function construirSystemPrompt(contexto) {
  const { tutor, estudiantes = [], todosBoletines = {} } = contexto || {};

  let infoHijos = "";
  estudiantes.forEach((est, idx) => {
    const bol = todosBoletines[est.id] || {};
    const materias = bol.materias || [];
    const asistencias = bol.asistencias || [];
    const observaciones = bol.observaciones || [];

    infoHijos += `\n--- HIJO #${idx + 1}: ${est.nombres} ${est.primer_apellido} ${est.segundo_apellido || ""} ---\n`;
    infoHijos += `Curso: ${est.grado || bol?.curso?.nombre || "No especificado"} | Gestión: ${est.gestion || "2026"} | RUDE: ${est.rude || "N/A"}\n`;

    // Materias y notas
    infoHijos += `CALIFICACIONES:\n`;
    if (materias.length === 0) {
      infoHijos += `  (Notas en proceso de captura)\n`;
    } else {
      materias.forEach((m) => {
        const nota = m.promedio_final;
        const estado = nota != null ? (nota >= 51 ? "APROBADO" : "EN RIESGO / REPROBADO (<51)") : "Pendiente";
        infoHijos += `  • ${m.area}: ${nota != null ? `${nota} pts` : "Sin nota"} [${estado}] (Docente: ${m.docente || "Asignado"})\n`;
      });
    }

    // Asistencia
    infoHijos += `ASISTENCIA:\n`;
    if (asistencias.length === 0) {
      infoHijos += `  (Sin registro de faltas)\n`;
    } else {
      asistencias.forEach((a) => {
        const faltas = Math.max((a.total || 0) - (a.presentes || 0), 0);
        infoHijos += `  • ${a.periodo}: ${a.porcentaje}% presencia (${a.presentes} asistencias, ${faltas} faltas de ${a.total} clases)\n`;
      });
    }

    // Observaciones docentes
    if (observaciones.length > 0) {
      infoHijos += `OBSERVACIONES DOCENTES:\n`;
      observaciones.forEach((o) => {
        infoHijos += `  • ${o.area} (${o.periodo}): "${o.observacion}" [Indicador: ${o.indicador || "PA"}]\n`;
      });
    }
  });

  return (
    `Eres el Agente de Inteligencia Artificial y Asistente Pedagógico oficial de la Unidad Educativa Fe y Alegría, diseñado para orientar a los padres de familia.\n` +
    `Estás conversando con el tutor(a): ${tutor?.nombre_completo || tutor?.nombre || "Estimado Padre/Madre"}.\n\n` +
    `DATOS REALES DE LOS HIJOS DEL TUTOR EN EL COLEGIO:\n${infoHijos}\n\n` +
    `NORMAS Y LÍMITES ESTRICTOS QUE DEBES SEGUIR OBLIGATORIAMENTE:\n` +
    `1. TU PROPÓSITO: Orientar al padre sobre el rendimiento escolar, hábitos de estudio, notas, asistencia y recomendaciones pedagógicas para el hogar según el desempeño real de sus hijos.\n` +
    `2. LÍMITE ESTRICTO (PROHIBIDO): Tienes TERMINANTEMENTE PROHIBIDO resolver cálculos matemáticos (como '1+1', 'cuánto es 5*5'), resolver las tareas de los alumnos, hablar de temas ajenos a la escuela (chistes, política, recetas, fútbol, código, etc.). Si el padre pregunta algo ajeno, rechaza amablemente indicando que eres un asistente escolar exclusivo de Fe y Alegría.\n` +
    `3. RENDIMIENTO Y ORIENTACIÓN: Si el estudiante tiene materias con menos de 51 puntos (reprobadas), alerta con empatía y ofrece consejos pedagógicos prácticos para el hogar (rutinas de estudio, técnicas de repaso, lectura compartida, coordinación con el docente).\n` +
    `4. MULTIHIJO: Tienes conocimiento de todos los hijos del tutor. Si el padre pregunta en general ("cómo van mis hijos"), compara o resume el estado de cada uno. Si menciona a un hijo por su nombre, enfócate en él.\n` +
    `5. ESCALA ESCOLAR: Recuerda que la nota mínima de aprobación en el sistema educativo boliviano es de 51 puntos sobre 100.\n` +
    `6. TONO: Cercano, empático, claro, motivador y respetuoso, usando viñetas y negritas para facilitar la lectura en teléfonos celulares.`
  );
}

/**
 * Consulta al Agente IA (con Groq API si hay API key, o fallback inteligente local).
 */
export async function consultarAgenteIA(pregunta, contexto, historial = []) {
  const q = (pregunta || "").trim();

  // 1. Guardrail de seguridad inmediato
  if (esConsultaFueraDeAlcance(q)) {
    return {
      tipo: "fuera_de_alcance",
      respuesta: mensajeFueraDeAlcance(),
      fuente: "guardrail",
    };
  }

  const apiKey = getGroqApiKey();

  // 2. Si no hay API key de Groq configurada, usar el motor pedagógico local
  if (!apiKey) {
    const local = procesarConsultaPadres(q, contexto);
    return {
      ...local,
      fuente: "local",
    };
  }

  // 3. Consulta al servicio Groq API (compatible con OpenAI chat completions)
  try {
    const systemPrompt = construirSystemPrompt(contexto);

    // Formatear mensajes: System prompt + historial reciente (últimos 6 mensajes) + pregunta actual
    const messages = [
      {
        role: "system",
        content: systemPrompt,
      },
    ];

    const ultimosMensajes = (historial || []).slice(-6);
    ultimosMensajes.forEach((msg) => {
      if (msg.sender === "user") {
        messages.push({ role: "user", content: msg.text });
      } else if (msg.sender === "bot") {
        messages.push({ role: "assistant", content: msg.text });
      }
    });

    messages.push({ role: "user", content: q });

    const payload = {
      model: GROQ_MODEL,
      messages: messages,
      temperature: 0.3,
      max_tokens: 900,
      top_p: 0.8,
    };

    const response = await fetch(GROQ_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      console.warn("Groq API respondió con error:", response.status, errData);
      // Fallback a motor local
      const local = procesarConsultaPadres(q, contexto);
      return {
        ...local,
        fuente: "fallback_local",
      };
    }

    const data = await response.json();
    const textoRespuesta =
      data?.choices?.[0]?.message?.content ||
      "No pude generar una respuesta en este momento. Por favor, intenta de nuevo.";

    return {
      tipo: "ia_generativa",
      respuesta: textoRespuesta,
      fuente: "groq",
      modelo: GROQ_MODEL,
    };
  } catch (error) {
    console.error("Error al conectar con Groq API:", error);
    // Fallback a motor pedagógico local
    const local = procesarConsultaPadres(q, contexto);
    return {
      ...local,
      fuente: "fallback_local",
    };
  }
}
