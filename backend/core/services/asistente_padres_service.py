"""
Asistente Académico para Padres de Familia — U.E. Fe y Alegría
==============================================================
Implementa Tool Calling sobre Groq Cloud (openai/gpt-oss-120b).

Seguridad:
  - El usuario autenticado se pasa desde la vista (nunca desde el cliente).
  - `AccessControlService.get_estudiantes_ids_tutor()` garantiza que solo
    se accedan datos de los hijos vinculados al tutor.
  - Si se pide información de un alumno no vinculado, se rechaza.

Guardrail:
  - Un filtro regex previo bloquea preguntas fuera de scope (matemáticas,
    cultura general, código, etc.) antes de llamar a Groq.
  - El System Prompt refuerza las restricciones al modelo.

Tool Calling:
  - `listar_hijos`           → nombres e IDs de los hijos del tutor.
  - `resumen_academico`      → boletín completo del hijo (notas, asistencia).
  - `materias_en_riesgo`     → materias con promedio < 51 pts.
  - `asistencia_estudiante`  → porcentaje de asistencia por período.
"""

import json
import os
import re

import requests

from .access_service import AccessControlService
from .report_card_service import ReportCardService

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b").strip().strip("'\"")
NOTA_APROBACION = 51

# ---------------------------------------------------------------------------
# Guardrail — patrones fuera de alcance
# ---------------------------------------------------------------------------
_OUT_OF_SCOPE = [
    r"\b\d+\s*[\+\-\*/\^x÷]\s*\d+",                              # 1+1, 5*3
    r"\b(cuanto|cuánto)\s+(es|son)\s+\d+",
    r"\b(calcula|calculame|calculá|resuelve|resolver)\b",
    r"\b(quien|quién)\s+(fue|es|descubrio|inventó?)\b",
    r"\b(capital\s+de|receta\s+de|poema|chiste|cuento)\b",
    r"\b(javascript|python|html|css|sql|react|codigo|código|programacion)\b",
    r"\b(futbol|fútbol|messi|ronaldo|partido\s+de|pelicula|película)\b",
    r"\b(clima\s+en|temperatura\s+en|dolar|bitcoin)\b",
    r"\b1\s*\+\s*1\b",
    r"\b2\s*\+\s*2\b",
    r"\b(dime\s+un\s+chiste|hazme\s+una\s+tarea|escribe\s+un\s+ensayo)\b",
]
_OUT_OF_SCOPE_RE = [re.compile(p, re.IGNORECASE) for p in _OUT_OF_SCOPE]

# Patrón para detectar intents de licencia (siempre permitidos)
_LICENCIA_INTENT_RE = re.compile(
    r"\b(licencia|permiso\s+de\s+ausencia|solicitar?\s+permiso|justificar\s+(falta|ausencia)|falta\s+justificada|ausencia\s+justificada)\b",
    re.IGNORECASE,
)


def _es_fuera_de_alcance(pregunta: str) -> bool:
    texto = pregunta.strip().lower()
    # Si es un intent de licencia, siempre está dentro del alcance
    if _LICENCIA_INTENT_RE.search(texto):
        return False
    return any(r.search(texto) for r in _OUT_OF_SCOPE_RE)


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT_TEMPLATE = """Eres el Asistente Académico oficial de la Unidad Educativa Fe y Alegría (Bolivia).
Estás hablando con el tutor/padre de familia: {nombre_tutor}.
Sus hijos registrados en el colegio son: {lista_hijos}.

REGLAS ABSOLUTAS — debes seguirlas sin excepción:
1. SOLO respondes sobre: calificaciones, promedios, materias reprobadas/en riesgo (<51 pts), asistencia, observaciones de docentes, orientación pedagógica para el hogar y LICENCIAS/PERMISOS DE AUSENCIA de los hijos mencionados arriba.
2. Si te preguntan sobre cualquier otro tema (matemáticas sueltas como "1+1", cultura general, código, recetas, política, chistes, etc.) responde ÚNICAMENTE con esta frase: "Solo puedo ayudarte con el rendimiento académico y licencias de tus hijos en la U.E. Fe y Alegría."
3. NUNCA inventes notas, promedios ni asistencias. Usa SIEMPRE las herramientas disponibles para leer datos reales.
4. Si el padre pregunta por un alumno que NO está en su lista de hijos, niega amablemente: "No tengo acceso a la información de ese estudiante."
5. Escala de aprobación boliviana: 51 de 100 puntos es el mínimo para aprobar.
6. Usa tono empático, cercano y motivador. Usa viñetas y negritas para facilitar la lectura en celular.
7. Si el padre quiere SOLICITAR UNA LICENCIA: usa la herramienta `solicitar_licencia` con el estudiante, motivo y fechas. Pídele los datos que falten antes de llamarla."""


# ---------------------------------------------------------------------------
# Definición de herramientas (tools) para Groq
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "listar_hijos",
            "description": "Devuelve los nombres completos e IDs de los hijos/estudiantes vinculados al tutor autenticado.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "resumen_academico",
            "description": "Obtiene el boletín completo de un hijo: curso, materias, notas por período, promedio final, asistencia y observaciones de docentes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "estudiante_nombre": {
                        "type": "string",
                        "description": "Nombre del estudiante (puede ser parcial, p. ej. 'Mateo').",
                    }
                },
                "required": ["estudiante_nombre"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "materias_en_riesgo",
            "description": "Lista las materias con promedio menor a 51 puntos (reprobadas o en riesgo) de un estudiante.",
            "parameters": {
                "type": "object",
                "properties": {
                    "estudiante_nombre": {
                        "type": "string",
                        "description": "Nombre del estudiante (puede ser parcial).",
                    }
                },
                "required": ["estudiante_nombre"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "asistencia_estudiante",
            "description": "Devuelve el porcentaje de asistencia y número de faltas de un estudiante por período.",
            "parameters": {
                "type": "object",
                "properties": {
                    "estudiante_nombre": {
                        "type": "string",
                        "description": "Nombre del estudiante (puede ser parcial).",
                    }
                },
                "required": ["estudiante_nombre"],
            },
        },
    },
]

# Herramienta adicional: solicitar_licencia
TOOLS.append({
    "type": "function",
    "function": {
        "name": "solicitar_licencia",
        "description": (
            "Registra una solicitud de licencia/permiso de ausencia para uno de los hijos del tutor. "
            "Usala SOLO cuando el padre haya confirmado: estudiante, motivo y fechas de inicio y fin."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "estudiante_nombre": {
                    "type": "string",
                    "description": "Nombre del estudiante (puede ser parcial).",
                },
                "motivo": {
                    "type": "string",
                    "description": "Motivo de la ausencia (ej. enfermedad, cita medica, viaje familiar).",
                },
                "fecha_inicio": {
                    "type": "string",
                    "description": "Fecha de inicio en formato YYYY-MM-DD.",
                },
                "fecha_fin": {
                    "type": "string",
                    "description": "Fecha de fin en formato YYYY-MM-DD.",
                },
            },
            "required": ["estudiante_nombre", "motivo", "fecha_inicio", "fecha_fin"],
        },
    },
})


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------
class AsistentePadresService:
    """
    Orquesta el flujo Tool Calling con Groq para el asistente académico.
    Todas las consultas de DB se hacen siempre con `usuario` de la sesión.
    """

    def __init__(self, usuario):
        self.usuario = usuario
        self.ac = AccessControlService()
        self.rcs = ReportCardService()
        self._hijos_cache = None  # [{id, nombres, apellido, nombre_completo}]

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    def _get_hijos(self):
        """Obtiene y cachea la lista de hijos del tutor."""
        if self._hijos_cache is not None:
            return self._hijos_cache

        from ..models import Estudiantes, EstudianteTutor
        tutor = self.ac.get_tutor(self.usuario)
        if not tutor:
            self._hijos_cache = []
            return []

        ids = list(
            EstudianteTutor.objects
            .filter(tutor=tutor, activo=True)
            .values_list("estudiante_id", flat=True)
        )
        hijos = []
        for est in Estudiantes.objects.filter(id__in=ids):
            hijos.append({
                "id": est.id,
                "nombres": est.nombres,
                "primer_apellido": est.primer_apellido,
                "segundo_apellido": est.segundo_apellido or "",
                "nombre_completo": f"{est.nombres} {est.primer_apellido} {est.segundo_apellido or ''}".strip(),
            })
        self._hijos_cache = hijos
        return hijos

    def _encontrar_hijo(self, nombre_parcial: str):
        """Busca el hijo que mejor coincide con el nombre parcial dado."""
        nombre_lower = nombre_parcial.strip().lower()
        hijos = self._get_hijos()
        for h in hijos:
            if nombre_lower in h["nombre_completo"].lower():
                return h
        # Buscar solo por primer nombre
        for h in hijos:
            for parte in h["nombre_completo"].lower().split():
                if nombre_lower == parte:
                    return h
        return None

    # ------------------------------------------------------------------
    # Implementaciones de herramientas
    # ------------------------------------------------------------------
    def _tool_listar_hijos(self, **_kwargs):
        hijos = self._get_hijos()
        if not hijos:
            return {"resultado": "El tutor no tiene hijos registrados en el sistema."}
        return {
            "hijos": [
                {
                    "id": h["id"],
                    "nombre_completo": h["nombre_completo"],
                }
                for h in hijos
            ]
        }

    def _tool_resumen_academico(self, estudiante_nombre: str, **_kwargs):
        hijo = self._encontrar_hijo(estudiante_nombre)
        if not hijo:
            return {"error": f"No encontré ningún hijo tuyo con el nombre '{estudiante_nombre}'. Los hijos registrados son: {[h['nombre_completo'] for h in self._get_hijos()]}"}
        try:
            boletin = self.rcs.generar_boletin(self.usuario, hijo["id"])
        except PermissionError:
            return {"error": "No tienes autorización para ver la información de ese estudiante."}
        except Exception as e:
            return {"error": f"No fue posible obtener el boletín: {str(e)}"}

        # Simplificar para el LLM
        materias = []
        for m in boletin.get("materias", []):
            materias.append({
                "materia": m["area"],
                "docente": m.get("docente") or "Asignado",
                "promedio_final": m.get("promedio_final"),
                "estado": "APROBADO" if (m.get("promedio_final") or 0) >= NOTA_APROBACION else "REPROBADO/EN RIESGO (<51)",
            })

        # Asistencias simplificadas (solo periodos con registros)
        asistencias_resumen = [
            f"{a['periodo']}: {a['porcentaje']}% ({a['presentes']}/{a['total']} días)"
            for a in boletin.get("asistencias", [])
            if (a.get("total") or 0) > 0
        ]

        # Observaciones agrupadas y sin repeticiones innecesarias
        obs_vistas = set()
        observaciones_resumen = []
        for o in boletin.get("observaciones", []):
            txt = (o.get("observacion") or "").strip()
            area = o.get("area") or ""
            clave = f"{area}:{txt}"
            if txt and clave not in obs_vistas:
                obs_vistas.add(clave)
                observaciones_resumen.append(f"{area}: {txt}")

        return {
            "estudiante": hijo["nombre_completo"],
            "curso": boletin.get("curso", {}).get("nombre", ""),
            "gestion": boletin.get("gestion", ""),
            "materias": materias,
            "asistencias": asistencias_resumen,
            "observaciones": observaciones_resumen[:6],
        }

    def _tool_materias_en_riesgo(self, estudiante_nombre: str, **_kwargs):
        hijo = self._encontrar_hijo(estudiante_nombre)
        if not hijo:
            return {"error": f"No encontré ningún hijo tuyo con el nombre '{estudiante_nombre}'."}
        try:
            boletin = self.rcs.generar_boletin(self.usuario, hijo["id"])
        except PermissionError:
            return {"error": "No tienes autorización para ver esa información."}
        except Exception as e:
            return {"error": str(e)}

        en_riesgo = [
            {
                "materia": m["area"],
                "promedio_final": m.get("promedio_final"),
                "docente": m.get("docente") or "Asignado",
            }
            for m in boletin.get("materias", [])
            if (m.get("promedio_final") is not None and m["promedio_final"] < NOTA_APROBACION)
        ]

        if not en_riesgo:
            return {
                "estudiante": hijo["nombre_completo"],
                "mensaje": "¡Excelente! No tiene materias reprobadas ni en riesgo. Todas sus materias están aprobadas (≥51 pts).",
            }
        return {
            "estudiante": hijo["nombre_completo"],
            "curso": boletin.get("curso", {}).get("nombre", ""),
            "materias_en_riesgo": en_riesgo,
            "total_en_riesgo": len(en_riesgo),
        }

    def _tool_asistencia_estudiante(self, estudiante_nombre: str, **_kwargs):
        hijo = self._encontrar_hijo(estudiante_nombre)
        if not hijo:
            return {"error": f"No encontré ningún hijo tuyo con el nombre '{estudiante_nombre}'."}
        try:
            boletin = self.rcs.generar_boletin(self.usuario, hijo["id"])
        except PermissionError:
            return {"error": "No tienes autorización para ver esa información."}
        except Exception as e:
            return {"error": str(e)}

        asistencias = boletin.get("asistencias", [])
        if not asistencias:
            return {
                "estudiante": hijo["nombre_completo"],
                "mensaje": "No hay registros de asistencia disponibles todavía.",
            }

        total_clases = sum(a.get("total", 0) for a in asistencias)
        total_presentes = sum(a.get("presentes", 0) for a in asistencias)
        pct_general = round((total_presentes / total_clases) * 100, 1) if total_clases > 0 else 100

        return {
            "estudiante": hijo["nombre_completo"],
            "asistencia_general": f"{pct_general}%",
            "detalle_por_periodo": [
                {
                    "periodo": a.get("periodo", ""),
                    "porcentaje": a.get("porcentaje", 0),
                    "presentes": a.get("presentes", 0),
                    "faltas": max((a.get("total", 0) - a.get("presentes", 0)), 0),
                    "total_clases": a.get("total", 0),
                }
                for a in asistencias
            ],
        }

    # ------------------------------------------------------------------
    # Herramienta: solicitar_licencia
    # ------------------------------------------------------------------
    def _tool_solicitar_licencia(self, estudiante_nombre: str, motivo: str,
                                  fecha_inicio: str, fecha_fin: str, **_kwargs):
        """Crea una solicitud de licencia en nombre del tutor autenticado."""
        from .license_service import LicenseService
        hijo = self._encontrar_hijo(estudiante_nombre)
        if not hijo:
            hijos_names = [h["nombre_completo"] for h in self._get_hijos()]
            return {
                "error": (
                    f"No encontre ningun hijo tuyo con el nombre {estudiante_nombre!r}. "
                    f"Los hijos registrados son: {hijos_names}"
                )
            }
        try:
            svc = LicenseService()
            resultado = svc.crear(self.usuario, {
                "estudiante_id": hijo["id"],
                "motivo": motivo,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "requiere_respaldo": False,
            })
            return {
                "estado": "exito",
                "licencia_id": resultado.get("id"),
                "estudiante": hijo["nombre_completo"],
                "motivo": motivo,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "mensaje": "Solicitud de licencia registrada. El personal de la institucion la revisara pronto.",
            }
        except (PermissionError, ValueError) as exc:
            return {"error": str(exc)}
        except Exception as exc:
            return {"error": f"No se pudo crear la licencia: {str(exc)}"}

    # ------------------------------------------------------------------
    # Dispatcher de herramientas
    # ------------------------------------------------------------------
    def _ejecutar_tool(self, nombre: str, args: dict):
        handlers = {
            "listar_hijos": self._tool_listar_hijos,
            "resumen_academico": self._tool_resumen_academico,
            "materias_en_riesgo": self._tool_materias_en_riesgo,
            "asistencia_estudiante": self._tool_asistencia_estudiante,
            "solicitar_licencia": self._tool_solicitar_licencia,
        }
        handler = handlers.get(nombre)
        if not handler:
            return {"error": f"Herramienta desconocida: {nombre}"}
        return handler(**args)

    # ------------------------------------------------------------------
    # Punto de entrada principal
    # ------------------------------------------------------------------
    def responder(self, pregunta: str, historial: list = None) -> dict:
        """
        Procesa la pregunta del tutor y devuelve la respuesta del asistente.

        Returns:
            {
                "respuesta": str,
                "fuente": "guardrail" | "groq_tool" | "groq_directo" | "error",
                "modelo": str (opcional)
            }
        """
        pregunta = (pregunta or "").strip()

        # 1. Guardrail local inmediato
        if _es_fuera_de_alcance(pregunta):
            return {
                "respuesta": "Solo puedo ayudarte con el rendimiento académico de tus hijos en la U.E. Fe y Alegría.",
                "fuente": "guardrail",
            }

        api_key = os.environ.get("GROQ_API_KEY", "").strip().strip("'\"")
        if not api_key:
            return {
                "respuesta": "El asistente IA no está disponible en este momento (clave API no configurada).",
                "fuente": "error",
            }

        # 2. Construir System Prompt con contexto del tutor
        hijos = self._get_hijos()
        nombre_tutor = getattr(self.usuario, "nombre_completo", None) or getattr(self.usuario, "usuario", "Estimado Tutor")
        lista_hijos_str = ", ".join(h["nombre_completo"] for h in hijos) if hijos else "Sin hijos registrados"

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            nombre_tutor=nombre_tutor,
            lista_hijos=lista_hijos_str,
        )

        # 3. Construir mensajes (System + historial reciente + pregunta actual)
        messages = [{"role": "system", "content": system_prompt}]

        for msg in (historial or [])[-6:]:  # últimos 6 turnos
            role = "user" if msg.get("sender") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("text", "")})

        messages.append({"role": "user", "content": pregunta})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # 4. Bucle de llamadas a Groq con soporte para Tool Calling encadenado
        # (ej. listar_hijos -> resumen_academico(hijo_1) -> resumen_academico(hijo_2) -> respuesta)
        max_iteraciones = 5
        hubo_tool_calls = False

        for iteracion in range(max_iteraciones):
            payload = {
                "model": GROQ_MODEL,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1200,
            }
            # En las iteraciones normales permitimos tools; en la última forzamos respuesta textual si fuera necesario
            if iteracion < max_iteraciones - 1:
                payload["tools"] = TOOLS
                payload["tool_choice"] = "auto"

            try:
                r = requests.post(
                    GROQ_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=30,
                )
                r.raise_for_status()
                data = r.json()
            except requests.exceptions.HTTPError as e:
                cuerpo = ""
                try:
                    cuerpo = f" - {r.text}"
                except Exception:
                    pass
                return {"respuesta": f"Error en la comunicación con el asistente: {str(e)}{cuerpo}", "fuente": "error"}
            except Exception as e:
                return {"respuesta": f"No pude conectarme al asistente IA: {str(e)}", "fuente": "error"}

            msg = data["choices"][0]["message"]
            tool_calls = msg.get("tool_calls") or []

            # Si no pide herramientas, tenemos el mensaje final
            if not tool_calls:
                texto = msg.get("content") or "No pude generar una respuesta."
                fuente = "groq_tool" if hubo_tool_calls else "groq_directo"
                return {"respuesta": texto, "fuente": fuente, "modelo": GROQ_MODEL}

            # Si pide herramientas, las ejecutamos y continuamos el bucle
            hubo_tool_calls = True
            messages.append(msg)

            for tc in tool_calls:
                fn_name = tc.get("function", {}).get("name", "")
                try:
                    fn_args = json.loads(tc.get("function", {}).get("arguments", "{}"))
                except (json.JSONDecodeError, KeyError):
                    fn_args = {}

                resultado = self._ejecutar_tool(fn_name, fn_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": fn_name,
                    "content": json.dumps(resultado, ensure_ascii=False),
                })

        # Si llegamos al final de las iteraciones
        texto_final = messages[-1].get("content") if messages else "No pude generar una respuesta completa."
        return {"respuesta": texto_final, "fuente": "groq_tool", "modelo": GROQ_MODEL}
