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