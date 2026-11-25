# Asistente empresarial de U.E. Fe y Alegría

Este módulo contiene la API FastAPI del asistente. La burbuja React está integrada en el
panel académico del proyecto principal y aparece para director, secretaría, regencia,
docentes y estudiantes autenticados. El portal de tutores conserva su asistente pedagógico
independiente.

## Funcionalidades

- Burbuja flotante adaptable a escritorio y dispositivos móviles.
- Conversación con mensajes de usuario y asistente.
- Respuestas mediante Groq (`openai/gpt-oss-20b`).
- Respuesta local de respaldo si no existe clave o Groq no está disponible.
- Contexto autorizado según el rol autenticado.
- Diseño con los colores institucionales: rojo `#FF2C2C`, rojo oscuro `#D92323`, fondo `#F4F7F2` y tipografía Roboto.
- Límites pedagógicos para rechazar consultas ajenas al rendimiento escolar.
- Respuestas limitadas a información institucional antes de llamar a Groq.
- Historial compatible con mensajes `assistant`, `bot` y `user`.
- Contexto construido por Django y limitado por el rol autenticado.

## Ejecución rápida

### 1. Configurar el backend

```powershell
cd C:\PS3\U.E.Fe-y-Alegria\AsistenteEmpresarial\backend
Copy-Item .env.example .env
py -m pip install -r requirements.txt
py -m uvicorn app:app --reload --host 127.0.0.1 --port 8001
```

Completa `GROQ_API_KEY` en `backend/.env`. Si se deja vacía, el servicio usa el motor local.

### 2. Ejecutar el portal integrado

```powershell
npm run build
npx serve@14 -s build -l 3000
```

Inicia el frontend y el backend Django como indica el README principal. El frontend principal
llama al endpoint autenticado de Django, que limita el contexto al rol y reenvía la consulta
a esta API en `http://127.0.0.1:8001`. No es necesario abrir el frontend independiente de
esta carpeta.

## Contexto académico

El backend Django construye el contexto desde la sesión autenticada y no permite usar este
endpoint a tutores. Sin `GROQ_API_KEY`, el asistente responde con el motor local.

## Comprobación

```powershell
curl.exe http://127.0.0.1:8001/health
curl.exe -X POST http://127.0.0.1:8001/api/chat -H "Content-Type: application/json" -d "{\"question\":\"¿Cómo puede mejorar su promedio?\",\"context\":{\"tutor\":{},\"estudiantes\":[],\"todosBoletines\":{}}}"
```

No publiques `GROQ_API_KEY` en el frontend ni la incorpores al control de versiones.
