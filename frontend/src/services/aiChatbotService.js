/**
 * Agente IA especializado para el Portal de Padres de Familia de la U.E. Fe y Alegría.
 * 
 * Limitaciones estrictas:
 * - Filtra y rechaza cualquier consulta ajena al ámbito escolar (matemáticas como 1+1, cultura general, etc.).
 * - Reconoce el contexto multihijo del tutor (un tutor puede tener 1 o más hijos).
 * - Proporciona respuestas precisas sobre calificaciones, materias en riesgo, promedios,
 *   asistencias, observaciones docentes y procedimientos escolares.
 * - Brinda soporte en el flujo de autenticación (CI, contraseña inicial, 2FA) sin recuperación por correo.
 */

// Palabras y patrones fuera de alcance (matemáticas, cultura general, código, etc.)
const OUT_OF_SCOPE_PATTERNS = [
  /\b\d+\s*[\+\-\*\/\^xX÷]\s*\d+/, // Operaciones como 1+1, 25 * 4, 10-5
  /\b(cuanto|cuánto)\s+es\s+\d+/i,
  /\b(calcula|calculame|calculá|resuelve|resolver)\b/i,
  /\b(quien|quién)\s+(fue|es|descubrio|descubrió|invento|inventó)\b/i,
  /\b(capital\s+de|receta\s+de|poema|cancion|canción|chiste|cuento|historia\s+de\s+terror)\b/i,
  /\b(javascript|python|c\+\+|html|css|sql|react|programacion|programación|codigo|código)\b/i,
  /\b(futbol|fútbol|messi|ronaldo|mundial|partido\s+de|pelicula|película|serie\s+de)\b/i,
  /\b(clima\s+en|tiempo\s+en|temperatura\s+en|dolar|dólar|bitcoin)\b/i,
];

export function esConsultaFueraDeAlcance(pregunta) {
  if (!pregunta || typeof pregunta !== "string") return false;
  const texto = pregunta.trim().toLowerCase();

  for (const pattern of OUT_OF_SCOPE_PATTERNS) {
    if (pattern.test(texto)) {
      return true;
    }
  }

  // Comprobar si son preguntas comunes no escolares
  if (
    texto.includes("1+1") ||
    texto.includes("2+2") ||
    texto.includes("dime un chiste") ||
    texto.includes("hazme una tarea") ||
    texto.includes("escribe un ensayo")
  ) {
    return true;
  }

  return false;
}

export function mensajeFueraDeAlcance() {
  return (
    "⚠️ **Consulta fuera de alcance**\n\n" +
    "Como **Asistente Escolar de la U.E. Fe y Alegría**, mis funciones están delimitadas exclusivamente a brindarte información sobre:" +
    "\n\n• Calificaciones y boletín de tus hijos" +
    "\n• Materias aprobadas y materias en riesgo (<51 pts)" +
    "\n• Asistencia y registro de inasistencias" +
    "\n• Observaciones cualitativas de los docentes" +
    "\n• Orientación sobre trámites escolares y acceso al portal" +
    "\n\n*No puedo resolver ejercicios matemáticos, preguntas de cultura general o temas ajenos al colegio.*" +
    "\n\n¿Deseas consultar las notas de alguno de tus hijos?"
  );
}

/**
 * Procesa una consulta cuando el usuario está en la página de Login (sin sesión aún).
 */
export function procesarConsultaLogin(pregunta) {
  const q = (pregunta || "").trim().toLowerCase();

  if (esConsultaFueraDeAlcance(q)) {
    return {
      respuesta:
        "⚠️ **Consulta fuera de alcance**: En esta pantalla solo puedo ayudarte con tu ingreso al Portal de Padres de Fe y Alegría (dudas sobre tu Carnet de Identidad, contraseña o código de verificación).\n\n¿En qué te puedo ayudar respecto a tu acceso?",
    };
  }

  // Olvido de contraseña
  if (
    q.includes("olvid") ||
    q.includes("recuperar") ||
    q.includes("perdi") ||
    q.includes("no me acuerdo") ||
    q.includes("restablecer")
  ) {
    return {
      respuesta:
        "🔑 **Recuperación de Contraseña de Tutores**\n\n" +
        "Por políticas de seguridad institucional de la U.E. Fe y Alegría, **no se realiza recuperación automática por correo electrónico** en este portal.\n\n" +
        "Para restablecer tu contraseña:\n" +
        "1. Debes presentarte personalmente en la **Dirección o Secretaría del colegio**.\n" +
        "2. Portar tu **Cédula de Identidad (CI)** original para verificar tu parentesco.\n" +
        "3. El personal autorizado te emitirá una nueva contraseña temporal de acceso inmediato.\n\n" +
        "⏰ *Horario de atención:* Lunes a Viernes de 08:00 a 16:00.",
    };
  }

  // Primera vez o cómo ingresar
  if (
    q.includes("primera vez") ||
    q.includes("nuevo") ||
    q.includes("como entro") ||
    q.includes("cómo entro") ||
    q.includes("como ingreso") ||
    q.includes("cómo ingreso") ||
    q.includes("usuario") ||
    q.includes("carnet") ||
    q.includes("ci")
  ) {
    return {
      respuesta:
        "📋 **¿Cómo ingresar al Portal de Familias?**\n\n" +
        "• **Usuario:** Es tu número de **Carnet de Identidad (CI)** registrado al momento de inscribir a tus hijos.\n" +
        "• **Contraseña:** Si es tu primera vez, ingresa con la contraseña temporal que te entregaron en secretaría o en tu comprobante de inscripción.\n\n" +
        "Al entrar por primera vez, el sistema te solicitará establecer una contraseña personal definitiva.",
    };
  }

  // Segundo factor / 2FA / Código
  if (q.includes("codigo") || q.includes("código") || q.includes("otp") || q.includes("2fa") || q.includes("digitos")) {
    return {
      respuesta:
        "🔐 **Código de Verificación (2FA)**\n\n" +
        "Es un código de 6 dígitos que se envía a tu correo personal para verificar que eres tú quien ingresa.\n\n" +
        "• Revisa tu bandeja de entrada o la carpeta de spam/correo no deseado.\n" +
        "• El código tiene una validez de 5 a 10 minutos.\n" +
        "• Si no te llegó, presiona el botón 'Reenviar código'.",
    };
  }

  // Horarios o contacto
  if (q.includes("horario") || q.includes("telefono") || q.includes("teléfono") || q.includes("secretaria") || q.includes("colegio") || q.includes("direccion") || q.includes("dirección")) {
    return {
      respuesta:
        "🏫 **Atención U.E. Fe y Alegría**\n\n" +
        "• **Secretaría y Dirección:** Lunes a Viernes de 08:00 a 16:00 continuo.\n" +
        "• **Trámites de tutores:** Presentar Carnet de Identidad (CI) en ventanilla.\n" +
        "• **Plataforma:** Disponible las 24 horas para revisión de notas.",
    };
  }

  // Saludo general
  if (q.includes("hola") || q.includes("buenos") || q.includes("buenas") || q.includes("ayuda")) {
    return {
      respuesta:
        "¡Hola! 👋 Soy tu Asistente Virtual de Fe y Alegría. Puedo orientarte para ingresar a tu cuenta de tutor:\n\n" +
        "• Ingresa tu **Carnet de Identidad (CI)** en el campo de texto.\n" +
        "• Si olvidaste tu contraseña, te indico cómo acudir a secretaría.\n" +
        "• Si es tu primera vez, te explico el uso de la clave temporal.",
    };
  }

  // Respuesta por defecto con guardrail
  return {
    respuesta:
      "🤖 Estoy aquí para asistirte con tu ingreso al Portal de Padres de Fe y Alegría. Por favor, escribe tu número de **Carnet de Identidad (CI)** para comenzar tu acceso.",
  };
}

/**
 * Procesa consultas del padre de familia autenticado dentro del portal.
 * Conoce a todos los hijos del tutor y sus respectivos boletines.
 * 
 * @param {string} pregunta Texto de la consulta
 * @param {object} contexto Contexto con:
 *   - tutor: { nombre, ci }
 *   - estudiantes: array de hijos
 *   - estudianteActivo: hijo actualmente seleccionado
 *   - todosBoletines: diccionario { [id]: boletinData }
 */
export function procesarConsultaPadres(pregunta, contexto) {
  const { tutor, estudiantes = [], estudianteActivo, todosBoletines = {} } = contexto || {};
  const q = (pregunta || "").trim().toLowerCase();

  // 1. FILTRO ESTRICTO: Rechazar temas fuera de alcance
  if (esConsultaFueraDeAlcance(q)) {
    return {
      tipo: "fuera_de_alcance",
      respuesta: mensajeFueraDeAlcance(),
    };
  }

  if (!estudiantes || estudiantes.length === 0) {
    return {
      tipo: "sin_estudiantes",
      respuesta:
        "No tienes estudiantes vinculados a tu cuenta de tutor en este momento. Por favor, acércate a la secretaría del colegio con tu Carnet de Identidad para verificar tu registro.",
    };
  }

  // 2. DETECCIÓN DEL ESTUDIANTE RELEVANTE (Soporte Multihijo)
  // ¿El padre mencionó el nombre de alguno de sus hijos?
  let targetEstudiante = null;
  for (const est of estudiantes) {
    const nombresSeparados = (est.nombres || "").toLowerCase().split(" ");
    const apellido = (est.primer_apellido || "").toLowerCase();
    const coincideNombre = nombresSeparados.some((n) => n.length > 2 && q.includes(n));
    const coincideApellido = apellido.length > 2 && q.includes(apellido);

    if (coincideNombre || coincideApellido) {
      targetEstudiante = est;
      break;
    }
  }

  // Si no mencionó a ninguno en específico pero tiene varios hijos y pregunta en general:
  const preguntaGeneralMultihijo =
    estudiantes.length > 1 &&
    (q.includes("hijos") ||
      q.includes("ambos") ||
      q.includes("todos") ||
      q.includes("mis niños") ||
      q.includes("resumen") ||
      q.includes("comparar") ||
      q.includes("quien tiene") ||
      q.includes("quién tiene"));

  // Si no seleccionó ninguno específico y no es pregunta general, usamos el estudiante activo en UI
  if (!targetEstudiante) {
    targetEstudiante = estudianteActivo || estudiantes[0];
  }

  const boletinTarget = todosBoletines[targetEstudiante.id] || null;

  // 3. INTENCIONES:

  // A) RESUMEN GENERAL MULTIHIJO (Comparativa de todos los hijos del tutor)
  if (preguntaGeneralMultihijo || (q.includes("como van") && estudiantes.length > 1 && !targetEstudiante)) {
    let textoResumen = `👨‍👩‍👧‍👦 **Resumen de tus ${estudiantes.length} hijos registrados:**\n\n`;

    estudiantes.forEach((est, idx) => {
      const bol = todosBoletines[est.id];
      const materias = bol?.materias || [];
      const enRiesgo = materias.filter((m) => m.promedio_final != null && Number(m.promedio_final) < 51);

      let suma = 0;
      let conNota = 0;
      materias.forEach((m) => {
        if (m.promedio_final != null) {
          suma += Number(m.promedio_final);
          conNota += 1;
        }
      });
      const promedio = conNota > 0 ? (suma / conNota).toFixed(1) : "En proceso";

      textoResumen += `**${idx + 1}. ${est.nombres} ${est.primer_apellido}** (${est.grado || "Curso"})\n`;
      textoResumen += `• Promedio general: **${promedio} pts**\n`;
      if (enRiesgo.length > 0) {
        textoResumen += `• ⚠️ Materias en riesgo (<51): **${enRiesgo.map((m) => m.area).join(", ")}**\n`;
      } else {
        textoResumen += `• ✅ Todas las materias aprobadas (≥51 pts)\n`;
      }
      textoResumen += "\n";
    });

    textoResumen += "¿Deseas ver el detalle de calificaciones de alguno de ellos en específico?";
    return { tipo: "resumen_multihijo", respuesta: textoResumen };
  }

  // B) MATERIAS EN RIESGO / REPROBADAS
  if (
    q.includes("reproba") ||
    q.includes("en riesgo") ||
    q.includes("baja") ||
    q.includes("peligro") ||
    q.includes("perdiendo") ||
    q.includes("apoyo") ||
    q.includes("menos de 51") ||
    q.includes("<51")
  ) {
    const materias = boletinTarget?.materias || [];
    const reprobadas = materias.filter((m) => m.promedio_final != null && Number(m.promedio_final) < 51);

    if (reprobadas.length === 0) {
      return {
        tipo: "materias_en_riesgo",
        respuesta:
          `🎉 **¡Excelentes noticias para ${targetEstudiante.nombres}!**\n\n` +
          `No tiene ninguna materia reprobada ni en riesgo. Todas sus materias registran una calificación igual o superior a los **51 puntos** de aprobación.\n\n` +
          (estudiantes.length > 1 ? `*Puedes consultar también por tus otros hijos.*` : ""),
      };
    }

    let detalle = `⚠️ **Materias que requieren apoyo para ${targetEstudiante.nombres}:**\n\n`;
    reprobadas.forEach((m) => {
      detalle += `• **${m.area}**: Nota actual **${m.promedio_final} pts** (Docente: ${m.docente || "Asignado"})\n`;
    });
    detalle += `\n*Recuerda que la nota mínima de aprobación es de 51 puntos. Te sugerimos conversar con los docentes respectivos.*`;

    return { tipo: "materias_en_riesgo", respuesta: detalle };
  }

  // C) CONSULTA DE MATERIA ESPECÍFICA (Matemática, Lenguaje, etc.)
  const MATERIAS_LISTA = [
    "matematica", "matemática", "lenguaje", "comunicacion", "comunicación",
    "ciencias", "sociales", "fisica", "física", "quimica", "química",
    "biologia", "biología", "artes", "musica", "música", "educacion fisica",
    "educación física", "religion", "religión", "valores", "filosofia", "filosofía",
    "tecnica", "técnica", "ingles", "inglés", "computacion", "computación"
  ];

  const materiaBuscada = MATERIAS_LISTA.find((m) => q.includes(m));
  if (materiaBuscada && boletinTarget?.materias) {
    const matMatch = boletinTarget.materias.find((m) =>
      (m.area || "").toLowerCase().includes(materiaBuscada)
    );

    if (matMatch) {
      const nota = matMatch.promedio_final;
      const estado = nota != null ? (nota >= 51 ? "✅ APROBADO" : "🚨 EN RIESGO (<51)") : "Pendiente";
      const obs = (boletinTarget.observaciones || []).filter(
        (o) => (o.area || "").toLowerCase() === (matMatch.area || "").toLowerCase()
      );

      let respMateria = `📖 **${matMatch.area}** - Estudiante: **${targetEstudiante.nombres}**\n\n`;
      respMateria += `• **Promedio actual:** **${nota != null ? `${nota} pts` : "Sin nota"}** (${estado})\n`;
      respMateria += `• **Docente:** ${matMatch.docente || "No especificado"}\n`;

      if (matMatch.notas_por_periodo) {
        respMateria += `• **Detalle trimestral:** `;
        const notasTrim = Object.entries(matMatch.notas_por_periodo)
          .map(([k, v]) => `T${k}: ${v != null ? v : "-"}`)
          .join(" | ");
        respMateria += `${notasTrim}\n`;
      }

      if (obs.length > 0) {
        respMateria += `\n💬 **Observación docente:** "${obs[0].observacion}" (${obs[0].indicador || "PA"})\n`;
      }

      return { tipo: "materia_detalle", respuesta: respMateria };
    }
  }

  // D) PROMEDIO GENERAL
  if (q.includes("promedio") || q.includes("nota final") || q.includes("rendimiento")) {
    const materias = boletinTarget?.materias || [];
    let suma = 0;
    let conNota = 0;
    materias.forEach((m) => {
      if (m.promedio_final != null) {
        suma += Number(m.promedio_final);
        conNota += 1;
      }
    });
    const prom = conNota > 0 ? (suma / conNota).toFixed(1) : "0";
    const estadoProm = Number(prom) >= 51 ? "Aprobado (Promovido)" : "En riesgo de reprobación";

    let resp = `📊 **Promedio General de ${targetEstudiante.nombres} ${targetEstudiante.primer_apellido}:**\n\n`;
    resp += `• **Promedio acumulado:** **${prom} / 100 puntos**\n`;
    resp += `• **Condición:** ${estadoProm}\n`;
    resp += `• **Total materias evaluadas:** ${conNota} de ${materias.length}\n`;

    if (estudiantes.length > 1) {
      resp += `\n*(Tienes ${estudiantes.length} hijos registrados. Puedes preguntar por el promedio de tus otros hijos).*`;
    }

    return { tipo: "promedio", respuesta: resp };
  }

  // E) ASISTENCIA Y FALTAS
  if (q.includes("asistencia") || q.includes("falta") || q.includes("inasistencia") || q.includes("licencia")) {
    const asistencias = boletinTarget?.asistencias || [];
    let totalClases = 0;
    let totalPresentes = 0;
    asistencias.forEach((a) => {
      totalClases += a.total || 0;
      totalPresentes += a.presentes || 0;
    });
    const faltas = Math.max(totalClases - totalPresentes, 0);
    const pct = totalClases > 0 ? Math.round((totalPresentes / totalClases) * 100) : 100;

    let respAsist = `📅 **Asistencia de ${targetEstudiante.nombres}:**\n\n`;
    respAsist += `• **Porcentaje global:** **${pct}% de presencia regular**\n`;
    respAsist += `• **Total clases registradas:** ${totalClases}\n`;
    respAsist += `• **Asistencias cumplidas:** ${totalPresentes}\n`;
    respAsist += `• **Faltas acumuladas:** **${faltas}**\n\n`;
    respAsist += `*Nota:* Para justificar faltas médicas o familiares, debes presentar el certificado o nota a Regencia en un plazo de 48 horas.`;

    return { tipo: "asistencia", respuesta: respAsist };
  }

  // F) OBSERVACIONES CUALITATIVAS DOCENTES
  if (q.includes("observacion") || q.includes("observaciones") || q.includes("comentario") || q.includes("profesor") || q.includes("conducta") || q.includes("indicador")) {
    const obs = boletinTarget?.observaciones || [];
    if (obs.length === 0) {
      return {
        tipo: "observaciones",
        respuesta: `📝 **${targetEstudiante.nombres}** no tiene observaciones cualitativas pendientes registradas por sus docentes en el periodo actual.`,
      };
    }

    let respObs = `💬 **Observaciones cualitativas para ${targetEstudiante.nombres}:**\n\n`;
    obs.slice(0, 4).forEach((o) => {
      respObs += `• **${o.area}** (${o.periodo}): "${o.observacion}" [Indicador: **${o.indicador || "PA"}**]\n`;
    });
    respObs += `\n*Indicadores:* PA (En Desarrollo) • SA (Satisfactorio) • A (Avanzado) • EA (Excelente).`;

    return { tipo: "observaciones", respuesta: respObs };
  }

  // G) DESCARGA DEL BOLETÍN
  if (q.includes("descarg") || q.includes("boletin") || q.includes("boletín") || q.includes("imprimir") || q.includes("word") || q.includes("pdf")) {
    return {
      tipo: "descarga",
      respuesta:
        `📄 **Boletín Oficial de Calificaciones**\n\n` +
        `Puedes descargar el boletín oficial de **${targetEstudiante.nombres}** en formato Word (.docx) listo para imprimir desde la pestaña de **Calificaciones** o presionando el botón 'Descargar Boletín'.\n\n` +
        `El documento incluye sellos, materias, firmas y las notas consolidadas de la gestión escolar.`,
    };
  }

  // H) ESCALA DE CALIFICACIÓN
  if (q.includes("escala") || q.includes("cuanto para aprobar") || q.includes("cuánto para aprobar") || q.includes("nota minima") || q.includes("nota mínima")) {
    return {
      tipo: "escala",
      respuesta:
        `📏 **Escala de Calificación Escolar (Fe y Alegría)**\n\n` +
        `• **Puntaje Máximo:** 100 puntos por materia.\n` +
        `• **Puntaje Mínimo de Aprobación:** **51 puntos**.\n` +
        `• **Reprobación:** 1 a 50 puntos (requiere reforzamiento pedagógico).\n` +
        `• **Periodos:** 3 Trimestres evaluados a lo largo de la gestión.`,
    };
  }

  // I) SALUDO / MENÚ DE AYUDA
  if (q.includes("hola") || q.includes("buenos") || q.includes("buenas") || q.includes("ayuda")) {
    const hijosNombres = estudiantes.map((e) => e.nombres).join(" y ");
    return {
      tipo: "saludo",
      respuesta:
        `¡Hola, estimado(a) ${tutor?.nombre || "tutor"}! 👋\n\n` +
        `Tienes acceso a la información académica de **${hijosNombres}**.\n\n` +
        `Puedes preguntarme sobre:\n` +
        `• *"¿Cuál es el promedio de mis hijos?"*\n` +
        `• *"¿Tiene alguna materia en riesgo o reprobada?"*\n` +
        `• *"¿Cómo va ${estudiantes[0]?.nombres} en Matemáticas?"*\n` +
        `• *"¿Cuántas faltas tiene?"*\n` +
        `• *"¿Qué observaciones tienen los profesores?"*\n` +
        `• *"¿Cómo descargo el boletín?"*`,
    };
  }

  // Default enfocado en notas y escolar
  return {
    tipo: "general",
    respuesta:
      `Estoy monitoreando el avance académico de **${targetEstudiante.nombres}** (${targetEstudiante.grado || "Curso"}).\n\n` +
      `Puedes consultarme sobre sus notas por materia, materias en riesgo (<51 pts), asistencia, observaciones docentes o descargar su boletín.\n\n` +
      `¿Qué información específica deseas consultar?`,
  };
}
