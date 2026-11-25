import os
from typing import Any, Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

app = FastAPI(
    title="Asistente Empresarial - U.E. Fe y Alegria",
    version="1.0.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ASSISTANT_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


class ChatMessage(BaseModel):
    sender: Literal["user", "bot", "assistant"]
    text: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    context: dict[str, Any] = Field(default_factory=dict)
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    source: Literal["groq", "local", "fallback_local"]
    model: str | None = None


def build_system_prompt(context: dict[str, Any]) -> str:
    tutor = context.get("tutor") or {}
    students = context.get("estudiantes") or []
    student_details: list[str] = []

    for index, student in enumerate(students, start=1):
        name = " ".join(
            str(student.get(key, "")).strip()
            for key in ("nombres", "primer_apellido", "segundo_apellido")
            if student.get(key)
        )
        grade = student.get("grado") or "No especificado"
        student_details.append(
            f"HIJO #{index}: {name or 'Estudiante'} | Curso: {grade}"
        )

    role = context.get("rol") or "usuario"
    available_sections = context.get("secciones_disponibles") or []
    sections_summary = ", ".join(available_sections) if available_sections else "Ninguna"
    institutional = context.get("resumen_institucional") or {}
    stats = institutional.get("estadisticas", {}).get("stats", {}) if institutional else {}
    summary = ""
    if stats:
        summary = (
            f"Estadísticas institucionales autorizadas: "
            f"{stats.get('total_estudiantes', 0)} estudiantes, "
            f"{stats.get('total_docentes', 0)} docentes, "
            f"{stats.get('total_asignaciones', 0)} asignaciones."
        )

    return (
        "Eres el asistente virtual oficial de la Unidad Educativa Fe y Alegría. "
        "Responde únicamente sobre esta institución, su portal escolar y la información "
        "académica proporcionada. No menciones direcciones, teléfonos, horarios, fechas "
        "ni requisitos que no estén confirmados en el contexto.\n"
        "Responde siempre en español, de forma breve: máximo 2 oraciones cortas. "
        "Si una consulta no pertenece a la institución o al desempeño escolar, responde "
        "exactamente: \"Solo puedo ayudar con información de la U.E. Fe y Alegría y del portal.\".\n\n"
        f"Tutor: {tutor.get('nombre_completo') or tutor.get('nombre') or 'Estimado padre/madre'}.\n"
        f"Estudiantes asociados:\n{' | '.join(student_details) if student_details else 'Sin datos cargados'}\n\n"
        f"Rol autorizado: {role}. {summary}\n\n"
        f"Secciones del panel autorizadas para consulta: {sections_summary}.\n"
        "Modo: solo lectura e información. No permitas editar, eliminar, crear ni modificar datos.\n"
        "Reglas obligatorias:\n"
        "1. Usa solo datos proporcionados. No inventes notas, faltas ni observaciones.\n"
        "2. La escala de aprobacion es 51 puntos sobre 100.\n"
        "3. Alerta con empatia las materias menores a 51 puntos y recomienda acciones practicas.\n"
        "4. Rechaza amablemente temas ajenos a la escuela, tareas que deban resolverse por el estudiante "
        "y solicitudes de calculos o informacion no relacionada.\n"
        "5. Responde en espanol, con tono cercano, profesional y motivador."
    )


def local_answer(question: str, context: dict[str, Any]) -> str:
    question_lower = question.lower()
    students = context.get("estudiantes") or []
    boletines = context.get("todosBoletines") or {}
    role = context.get("rol") or ""

    if "cuánt" in question_lower or "cuant" in question_lower:
        if "estudiante" in question_lower:
            if role in {"director", "secretaria", "regente"}:
                stats = (context.get("resumen_institucional") or {}).get(
                    "estadisticas", {}
                ).get("stats", {})
                return f"Hay {stats.get('total_estudiantes', 0)} estudiantes registrados."
            if students:
                return f"Tienes acceso a información de {len(students)} estudiante(s)."

    allowed_terms = (
        "hola", "buen", "portal", "fe", "alegría", "alegria", "escuela",
        "colegio", "institución", "institucion", "inscrip", "matricul",
        "horario", "calendario", "calificacion", "calificación", "nota",
        "promedio", "asistencia", "falta", "estudi", "riesgo", "reprob",
        "boletin", "boletín", "hijo", "hija", "estudiante", "tutor",
        "padre", "madre", "rendimiento", "secretaria", "secretaría",
        "login", "sesion", "sesión", "contraseña", "contrasena",
    )
    if not any(term in question_lower for term in allowed_terms):
        return "Solo puedo ayudar con información de la U.E. Fe y Alegría y del portal."

    if any(word in question_lower for word in ("hola", "buen dia", "buenas")):
        return "Hola. Soy el asistente de Fe y Alegría y puedo orientarte sobre el portal y la información escolar."

    if any(word in question_lower for word in ("portal", "informacion general", "información general", "servicios", "institucion", "institución")):
        return "El portal de la U.E. Fe y Alegría reúne servicios académicos y administrativos, como calificaciones, asistencia, horarios, inscripciones y reportes. La información personal de estudiantes se consulta después de iniciar sesión."

    if "inscrip" in question_lower or "matricul" in question_lower:
        return "El portal incluye opciones de inscripción y reinscripción. Para conocer requisitos, fechas y documentación vigente, consulta directamente con Secretaría de la U.E. Fe y Alegría."

    if "horario" in question_lower or "calendario" in question_lower:
        return "El portal dispone de información de horarios escolares. Inicia sesión para consultar la información disponible para tu cuenta; para fechas institucionales vigentes, confirma con la escuela."

    if "riesgo" in question_lower or "reprob" in question_lower:
        risk_names: list[str] = []
        for student in students:
            student_id = student.get("id")
            boletin = boletines.get(student_id) or boletines.get(str(student_id)) or {}
            materias = boletin.get("materias") or []
            risk_count = sum(
                1
                for materia in materias
                if materia.get("promedio_final") is not None
                and float(materia["promedio_final"]) < 51
            )
            if risk_count:
                name = str(student.get("nombres") or "Estudiante").strip()
                risk_names.append(f"{name}: {risk_count} materia(s)")
        if risk_names:
            return "Materias en riesgo detectadas: " + "; ".join(risk_names) + ". Coordina con el docente un plan de recuperación."
        return "No hay materias menores a 51 puntos en los boletines disponibles."

    if "mis hijos" in question_lower or ("hijos" in question_lower and "cómo" in question_lower):
        summaries: list[str] = []
        for student in students:
            student_id = student.get("id")
            boletin = boletines.get(student_id) or boletines.get(str(student_id)) or {}
            materias = boletin.get("materias") or []
            notes = [
                float(materia["promedio_final"])
                for materia in materias
                if materia.get("promedio_final") is not None
            ]
            name = str(student.get("nombres") or "Estudiante").strip()
            if notes:
                average = sum(notes) / len(notes)
                risk_count = sum(note < 51 for note in notes)
                summaries.append(
                    f"{name}: promedio {average:.2f}, "
                    f"{risk_count} materia(s) en riesgo"
                )
            else:
                summaries.append(f"{name}: notas aún no disponibles")
        if summaries:
            return "Estado de los hijos: " + "; ".join(summaries) + "."

    if "promedio" in question_lower:
        for student in students:
            student_id = student.get("id")
            boletin = (
                boletines.get(student_id)
                or boletines.get(str(student_id))
                or {}
            )
            materias = boletin.get("materias") or []
            notas = [float(m["promedio_final"]) for m in materias if m.get("promedio_final") is not None]
            if notas:
                promedio = sum(notas) / len(notas)
                return f"El promedio disponible de {student.get('nombres', 'el estudiante')} es {promedio:.2f} puntos."
        return "Necesito que el boletín esté disponible para calcular el promedio."

    if "asistencia" in question_lower or "faltas" in question_lower:
        return "Puedes consultar las asistencias y faltas registradas en el boletín. La asistencia regular y la comunicación con el tutor son fundamentales."

    if "estudi" in question_lower or "ayudar" in question_lower:
        return "Te recomiendo una rutina breve y constante: revisar las materias pendientes, reservar una hora diaria, separar descansos y contactar al docente ante dudas."

    return "Puedo ayudarte con notas, promedio, materias en riesgo, asistencia y consejos de estudio. ¿Qué información necesitas?"


def is_institution_question(question: str) -> bool:
    question_lower = question.lower()
    allowed_terms = (
        "hola", "buen", "portal", "fe", "alegría", "alegria", "escuela",
        "colegio", "institución", "institucion", "inscrip", "matricul",
        "horario", "calendario", "calificacion", "calificación", "nota",
        "promedio", "asistencia", "falta", "estudi", "riesgo", "reprob",
        "boletin", "boletín", "hijo", "hija", "estudiante", "tutor",
        "padre", "madre", "rendimiento", "secretaria", "secretaría",
        "login", "sesion", "sesión", "contraseña", "contrasena",
    )
    return any(term in question_lower for term in allowed_terms)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "Asistente Empresarial"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    question = payload.question.strip()
    if not is_institution_question(question):
        return ChatResponse(
            answer="Solo puedo ayudar con información de la U.E. Fe y Alegría y del portal.",
            source="local",
        )
    question_lower = question.lower()
    local_topics = (
        "cuánt", "cuant", "promedio", "riesgo", "reprob",
        "mis hijos", "asistencia", "faltas",
    )
    if any(topic in question_lower for topic in local_topics):
        return ChatResponse(
            answer=local_answer(question, payload.context),
            source="local",
        )
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        return ChatResponse(answer=local_answer(question, payload.context), source="local")

    messages = [{"role": "system", "content": build_system_prompt(payload.context)}]
    for message in payload.history[-8:]:
        messages.append({
            "role": "user" if message.sender == "user" else "assistant",
            "content": message.text,
        })
    messages.append({"role": "user", "content": question})

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 900,
                    "top_p": 0.8,
                },
            )
        if response.status_code >= 400:
            return ChatResponse(
                answer=local_answer(question, payload.context),
                source="fallback_local",
            )
        data = response.json()
        answer = data.get("choices", [{}])[0].get("message", {}).get("content")
        if not answer:
            raise HTTPException(status_code=502, detail="Groq devolvió una respuesta vacía.")
        return ChatResponse(answer=answer, source="groq", model=GROQ_MODEL)
    except httpx.HTTPError as error:
        return ChatResponse(
            answer=local_answer(question, payload.context),
            source="fallback_local",
        )
