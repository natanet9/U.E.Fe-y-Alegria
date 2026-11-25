# 🚀 Proyecto U.E. Fe y Alegria

## 📌 Descripción

Proyecto web full stack usando:

* Backend con Django (API REST)
* Frontend con React
* Base de datos PostgreSQL

---

## 🧱 Tecnologías

* Python / Django
* Django REST Framework
* React
* PostgreSQL

---

## ⚙️ Instalación

### 🔹 Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate 

pip install -r ../requirements.txt
python manage.py migrate

python manage.py runserver
```

---

### 🔹 Frontend

```bash
cd frontend
npm install
npm start
```

### 🔹 Asistente virtual

El panel académico muestra la burbuja para director, secretaría, regencia, docentes y
estudiantes autenticados; los tutores conservan su asistente pedagógico actual. Para activar
el motor local del asistente, inicia su API en una terminal aparte:

```powershell
cd AsistenteEmpresarial\backend
py -m pip install -r requirements.txt
py -m uvicorn app:app --reload --host 127.0.0.1 --port 8001
```

La clave `GROQ_API_KEY` es opcional; sin ella se usa el motor local.

---

## ☁️ Despliegue en Render

Publica el proyecto como tres servicios separados: el backend Django, el backend
FastAPI del asistente y el frontend React. El asistente ya está integrado en el
frontend principal; no hace falta publicar otro frontend.

### Backend Django (Web Service)

Deja **Root Directory** vacío para que Render use la raíz del repositorio.

```bash
# Build Command
pip install -r requirements.txt

# Start Command
cd backend && python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

Configura en el entorno del servicio las credenciales de PostgreSQL (`DB_NAME`,
`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`) y estas variables:

```text
DJANGO_SECRET_KEY=<clave aleatoria privada>
DJANGO_DEBUG=False
ALLOWED_HOSTS=<dominio-del-backend>.onrender.com
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://<dominio-del-frontend>.onrender.com
AUTH_COOKIE_SAMESITE=None
ASSISTANT_API_URL=https://<dominio-del-asistente>.onrender.com
FRONTEND_BASE_URL=https://<dominio-del-frontend>.onrender.com
```

`AUTH_COOKIE_SAMESITE=None` permite que el navegador envíe la cookie de sesión
entre el frontend y el backend cuando se publican en dominios distintos. En
producción, `AUTH_COOKIE_SECURE` se activa automáticamente y requiere HTTPS.

Genera `DJANGO_SECRET_KEY` de forma aleatoria y guárdala solo en las variables
privadas de Render; no la publiques en Git ni en el frontend. `FRONTEND_BASE_URL`
debe apuntar al frontend: si ya existe en Render, edita su valor en vez de crear
una variable duplicada. Esta URL se usa en los enlaces de correo.

Para cargar los datos de demostración en una base **vacía**, después de desplegar
ejecuta una sola vez desde la Shell del servicio:

```bash
cd backend && python manage.py seed
```

`seed` crea datos de demostración y usuarios con contraseñas predeterminadas;
revisa el comando antes de usarlo con datos reales y cambia esas contraseñas.
No ejecutes `seed --flush` en una base que quieras conservar. No incluyas `seed`
en el Start Command, porque Render lo ejecutaría de nuevo en cada reinicio.

### Backend del asistente (Web Service)

Deja **Root Directory** vacío:

```bash
# Build Command
pip install -r AsistenteEmpresarial/backend/requirements.txt

# Start Command
cd AsistenteEmpresarial/backend && uvicorn app:app --host 0.0.0.0 --port $PORT
```

Configura `GROQ_API_KEY` si vas a usar Groq. El servicio también puede responder
sin esa clave mediante su motor local.

### Frontend React (Static Site)

Usa **Root Directory** `frontend`, **Build Command** `npm ci && npm run build` y
**Publish Directory** `build`. Configura `REACT_APP_API_URL` como
`https://<dominio-del-backend>.onrender.com/api` antes de compilar el sitio.

---

## ✉️ Correo (SMTP) y códigos de recuperación

* Los OTP, las credenciales y la recuperación de contraseña se envían **siempre** al
  `correo_personal` registrado del usuario (respaldo: su correo institucional).
  Ese buzón debe poder recibir correo.
* Si el log muestra `correo.enviado ... enviados=1` pero el usuario no recibe nada,
  el proveedor aceptó el mensaje pero lo bloqueó después (Gmail personal suele hacerlo
  y devuelve un bounce de `Mail Delivery Subsystem` al remitente).
* Para producción use un proveedor transaccional (Brevo, SendGrid, Resend, Mailgun) o
  Google Workspace con el dominio verificado: solo hay que cambiar `EMAIL_*` y
  `DEFAULT_FROM_EMAIL` en el `.env`.

---

## 📂 Estructura

```
mi_proyecto/
│
├── backend/
├── frontend/
├── requirements.txt
└── README.md
```