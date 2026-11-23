import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  loginRequest,
  verifyOtpRequest,
  resendOtpRequest,
  isAuthenticated,
  getStoredUser,
  logoutRequest,
} from "../../services/authService";
import { procesarConsultaLogin } from "../../services/aiChatbotService";

export default function PadresLoginPage() {
  const navigate = useNavigate();

  // Si ya tiene sesión activa como tutor, redirigir al portal de padres
  useEffect(() => {
    if (isAuthenticated()) {
      const u = getStoredUser();
      const rol = (u?.rol || u?.cargo || "").toLowerCase();
      if (rol === "tutor") {
        navigate("/padres", { replace: true });
      } else {
        navigate("/dashboard", { replace: true });
      }
    }
  }, [navigate]);

  // Modo: 'chatbot' o 'tradicional'
  const [modo, setModo] = useState("chatbot");

  // Estado del flujo de login asistido
  // 'identificador' | 'password' | 'otp' | 'exito'
  const [fase, setFase] = useState("identificador");
  const [identificador, setIdentificador] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [codigoOtp, setCodigoOtp] = useState("");
  const [challenge, setChallenge] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [typing, setTyping] = useState(false);

  // Historial de mensajes en el chat
  const [mensajes, setMensajes] = useState([
    {
      id: "m-1",
      sender: "bot",
      text: "¡Hola! 👋 Te doy la bienvenida al Portal Familiar de la Unidad Educativa Fe y Alegría.",
      tiempo: "Ahora",
    },
    {
      id: "m-2",
      sender: "bot",
      text: "Soy tu Asistente Virtual. Te orientaré de forma segura para que puedas ingresar y consultar las notas, materias y boletín escolar de tus hijos.",
      tiempo: "Ahora",
    },
    {
      id: "m-3",
      sender: "bot",
      text: "Para comenzar, por favor escribe tu número de Carnet de Identidad (CI):",
      tiempo: "Ahora",
      opciones: [
        { label: "¿Olvidaste tu contraseña?", accion: "ayuda_password" },
        { label: "¿Cuál es mi usuario?", accion: "ayuda_usuario" },
        { label: "¿Es tu primera vez aquí?", accion: "ayuda_primera_vez" },
      ],
    },
  ]);

  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [mensajes, typing]);

  const agregarMensaje = (sender, text, opciones = null) => {
    const nuevo = {
      id: `m-${Date.now()}-${Math.random()}`,
      sender,
      text,
      opciones,
      tiempo: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setMensajes((prev) => [...prev, nuevo]);
  };

  const responderBotConRetardo = (text, opciones = null, ms = 450) => {
    setTyping(true);
    setTimeout(() => {
      setTyping(false);
      agregarMensaje("bot", text, opciones);
    }, ms);
  };

  // 1. Envío de identificador (o consulta al asistente)
  const handleEnviarIdentificador = (e) => {
    if (e) e.preventDefault();
    const val = identificador.trim();
    if (!val) return;

    agregarMensaje("user", val);

    // ¿Es una pregunta o texto general en lugar de un CI o correo?
    const esPregunta =
      val.includes("?") ||
      val.includes("¿") ||
      val.length > 25 ||
      /^[a-zA-Z\s]{4,}$/.test(val) ||
      val.includes("+") ||
      val.includes("-") ||
      val.includes("*");

    if (esPregunta) {
      setTyping(true);
      setTimeout(() => {
        setTyping(false);
        const resultado = procesarConsultaLogin(val);
        agregarMensaje("bot", resultado.respuesta, [
          { label: "Ingresar mi Carnet de Identidad (CI)", accion: "reiniciar_identificador" },
          { label: "¿Olvidaste tu contraseña?", accion: "ayuda_password" },
        ]);
      }, 400);
      setIdentificador("");
      return;
    }

    // Es un CI o identificador válido
    setTyping(true);
    setTimeout(() => {
      setTyping(false);
      agregarMensaje(
        "bot",
        `Excelente. He registrado tu identificación: **${val}**.\n\nPor favor, escribe tu **contraseña de acceso** a continuación:`,
      );
      setFase("password");
    }, 450);
  };

  // 2. Envío de contraseña y autenticación
  const handleEnviarPassword = async (e) => {
    if (e) e.preventDefault();
    if (!password.trim()) return;

    agregarMensaje("user", "•••••••• (Contraseña enviada)");
    setCargando(true);
    setTyping(true);

    try {
      const data = await loginRequest(identificador, password);

      setTyping(false);
      setCargando(false);

      // Verificación estricta de rol: Solo tutores
      // loginRequest devuelve el objeto de usuario directamente. En el modelo, 'usuario' es el username (string "7000020").
      const usuarioObj = (data && typeof data === "object" && typeof data.usuario === "object" && data.usuario !== null)
        ? data.usuario
        : data;
      const rawRol = (typeof usuarioObj?.rol === "object" && usuarioObj?.rol !== null)
        ? usuarioObj.rol.nombre
        : (usuarioObj?.rol || usuarioObj?.cargo || "");
      const rol = String(rawRol || "").toLowerCase();
      if (rol !== "tutor") {
        await logoutRequest();
        agregarMensaje(
          "bot",
          `⚠️ **Acceso no permitido en este portal**\n\nEsta plataforma es de uso exclusivo para padres de familia y tutores. Tu cuenta corresponde al personal docente/administrativo del colegio. Por políticas de seguridad, no puedes ingresar a la sección de padres desde esta web.`,
        );
        setFase("identificador");
        setPassword("");
        return;
      }

      if (data?.requires_otp) {
        setChallenge(data);
        setFase("otp");
        agregarMensaje(
          "bot",
          `🔐 Por seguridad, tu cuenta requiere verificación en dos pasos (2FA).\n\n` +
            (data.metodo === "totp"
              ? "Ingresa el código de 6 dígitos de tu aplicación autenticadora:"
              : `Enviamos un código de 6 dígitos a tu correo: **${data.destinatario || "registrado"}**.\nIngrésalo aquí:`),
          [{ label: "Reenviar código de verificación", accion: "reenviar_otp" }],
        );
        return;
      }

      finalizarLoginExitoso(usuarioObj);
    } catch (err) {
      setTyping(false);
      setCargando(false);
      const errorMsg =
        err?.response?.data?.error ||
        "Credenciales incorrectas. Verifica que tu Carnet y contraseña estén bien escritos.";

      agregarMensaje(
        "bot",
        `⚠️ ${errorMsg}\n\nPor favor, intenta nuevamente:`,
        [
          { label: "Corregir mi Carnet de Identidad", accion: "reiniciar_identificador" },
          { label: "¿Olvidaste tu contraseña?", accion: "ayuda_password" },
        ],
      );
    }
  };

  // 3. Verificación de OTP
  const handleEnviarOtp = async (e) => {
    if (e) e.preventDefault();
    if (!codigoOtp.trim()) return;

    agregarMensaje("user", `Código: ${codigoOtp.trim()}`);
    setCargando(true);
    setTyping(true);

    try {
      const usuario = await verifyOtpRequest(challenge.otp_token, codigoOtp.trim());
      setTyping(false);
      setCargando(false);

      // Verificación estricta de rol
      const rol = (usuario?.rol || usuario?.cargo || "").toLowerCase();
      if (rol !== "tutor") {
        await logoutRequest();
        agregarMensaje(
          "bot",
          `⚠️ Tu cuenta no corresponde al rol de padre de familia/tutor. Acceso restringido.`,
        );
        return;
      }

      finalizarLoginExitoso(usuario);
    } catch (err) {
      setTyping(false);
      setCargando(false);
      const errorMsg =
        err?.response?.data?.error || "Código de verificación incorrecto o expirado.";
      agregarMensaje(
        "bot",
        `❌ ${errorMsg}\n\nIngresa el código de 6 dígitos nuevamente o solicita uno nuevo:`,
        [{ label: "Reenviar código", accion: "reenviar_otp" }],
      );
    }
  };

  // Redirección exitosa
  const finalizarLoginExitoso = (usuario) => {
    setFase("exito");
    const nombre = usuario?.nombre || usuario?.nombres || "Estimado Padre de Familia";
    agregarMensaje(
      "bot",
      `¡Bienvenido(a), **${nombre}**! 🎉\n\nIdentidad confirmada. Abriendo tu panel con las calificaciones y el boletín de tus hijos...`,
    );

    setTimeout(() => {
      if (usuario?.debe_cambiar_password) {
        navigate("/cambiar-password-obligatorio");
        return;
      }
      navigate("/padres");
    }, 1200);
  };

  // Acciones rápidas del asistente de login
  const handleAccionBot = async (accion) => {
    if (accion === "ayuda_password") {
      agregarMensaje("user", "¿Cómo recupero o cambio mi contraseña?");
      responderBotConRetardo(
        "🔒 **Restablecimiento de Contraseña para Tutores**\n\n" +
          "Por normativas de seguridad institucional de la U.E. Fe y Alegría, **no se realiza recuperación de contraseña por correo electrónico** en esta plataforma.\n\n" +
          "Para recuperar o solicitar una nueva contraseña:\n" +
          "1. Debes presentarte en la **Dirección o Secretaría de la U.E. Fe y Alegría**.\n" +
          "2. Presentar tu **Cédula de Identidad (CI)** original para validar tu titularidad como tutor legal.\n" +
          "3. El personal autorizado te otorgará una contraseña temporal de acceso inmediato.\n\n" +
          "⏰ *Horario de atención:* Lunes a Viernes de 08:00 a 16:00.",
        [{ label: "Entendido, ya tengo mi contraseña", accion: "reiniciar_identificador" }],
      );
    } else if (accion === "ayuda_usuario") {
      agregarMensaje("user", "¿Cuál es mi usuario?");
      responderBotConRetardo(
        "🆔 **Tu usuario de acceso:**\n\n" +
          "Tu usuario es tu número de **Carnet de Identidad (CI)** (sin letras ni espacios extras). Ejemplo: `4829104`.\n\n" +
          "Es el mismo documento con el que registraste a tus hijos en el sistema del colegio.",
        [{ label: "Escribir mi Carnet de Identidad", accion: "reiniciar_identificador" }],
      );
    } else if (accion === "ayuda_primera_vez") {
      agregarMensaje("user", "Es mi primera vez en la plataforma");
      responderBotConRetardo(
        "👋 **Primer ingreso al sistema:**\n\n" +
          "1. Escribe tu **Carnet de Identidad (CI)**.\n" +
          "2. Escribe la **contraseña temporal** que te entregó secretaría en tu comprobante de inscripción.\n" +
          "3. El sistema te pedirá crear una nueva contraseña personal y segura que tú elijas.",
        [{ label: "Ingresar mi Carnet de Identidad", accion: "reiniciar_identificador" }],
      );
    } else if (accion === "reiniciar_identificador") {
      setFase("identificador");
      setPassword("");
      setCodigoOtp("");
      responderBotConRetardo(
        "Por favor, escribe tu número de **Carnet de Identidad (CI)**:",
      );
    } else if (accion === "reenviar_otp") {
      if (!challenge?.otp_token) return;
      setCargando(true);
      try {
        const data = await resendOtpRequest(challenge.otp_token);
        agregarMensaje(
          "bot",
          `✅ Código reenviado a: **${data?.destinatario || "tu correo"}**. Revisa tu bandeja de entrada o spam.`,
        );
      } catch (err) {
        agregarMensaje(
          "bot",
          `⚠️ No se pudo reenviar el código: ${err?.response?.data?.error || "Intenta más tarde."}`,
        );
      } finally {
        setCargando(false);
      }
    }
  };

  // Formulario rápido (modo tradicional)
  const [formEmail, setFormEmail] = useState("");
  const [formPass, setFormPass] = useState("");
  const [formError, setFormError] = useState("");
  const [formLoading, setFormLoading] = useState(false);
  const [infoPasswordModal, setInfoPasswordModal] = useState(false);

  const handleTraditionalSubmit = async (e) => {
    e.preventDefault();
    setFormError("");
    setFormLoading(true);

    try {
      const data = await loginRequest(formEmail, formPass);
      const usuarioObj = (data && typeof data === "object" && typeof data.usuario === "object" && data.usuario !== null)
        ? data.usuario
        : data;
      const rawRol = (typeof usuarioObj?.rol === "object" && usuarioObj?.rol !== null)
        ? usuarioObj.rol.nombre
        : (usuarioObj?.rol || usuarioObj?.cargo || "");
      const rol = String(rawRol || "").toLowerCase();

      if (rol !== "tutor") {
        await logoutRequest();
        setFormError(
          "Esta página es exclusiva para padres de familia. El personal docente/administrativo no tiene acceso aquí.",
        );
        return;
      }

      if (data?.requires_otp) {
        setModo("chatbot");
        setIdentificador(formEmail);
        setChallenge(data);
        setFase("otp");
        agregarMensaje(
          "bot",
          `🔐 Verificación en 2 pasos para **${formEmail}**. Por favor ingresa el código de 6 dígitos enviado:`,
        );
        return;
      }
      finalizarLoginExitoso(usuarioObj);
    } catch (err) {
      setFormError(
        err?.response?.data?.error || "Credenciales incorrectas. Verifica tu Carnet o contraseña.",
      );
    } finally {
      setFormLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-between font-sans antialiased text-slate-800">
      {/* Header Institucional Familiar (Sin enlaces a docentes) */}
      <header className="bg-white border-b border-slate-200/80 shadow-2xs sticky top-0 z-20">
        <div className="max-w-md mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-red-600 to-rose-600 flex items-center justify-center text-white font-black text-xl shadow-md shadow-red-500/20">
              FA
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-slate-900 text-sm sm:text-base leading-none">
                  U.E. Fe y Alegría
                </span>
                <span className="bg-red-100 text-red-700 text-[10px] font-bold px-1.5 py-0.5 rounded-md">
                  PORTAL FAMILIAS
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Seguimiento Escolar y Calificaciones
              </p>
            </div>
          </div>

          <span className="text-[10px] bg-slate-100 text-slate-600 font-semibold px-2.5 py-1 rounded-full border border-slate-200">
            PWA Móvil
          </span>
        </div>

        {/* Selector de Modo */}
        <div className="max-w-md mx-auto px-4 pb-2.5 pt-1">
          <div className="bg-slate-100 p-1 rounded-xl grid grid-cols-2 text-xs font-bold text-center gap-1">
            <button
              onClick={() => setModo("chatbot")}
              className={`py-1.5 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                modo === "chatbot"
                  ? "bg-white text-red-600 shadow-xs shadow-slate-300"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              <span>🤖</span>
              <span>Ingreso con Asistente IA</span>
            </button>
            <button
              onClick={() => setModo("tradicional")}
              className={`py-1.5 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                modo === "tradicional"
                  ? "bg-white text-red-600 shadow-xs shadow-slate-300"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              <span>📝</span>
              <span>Formulario Rápido</span>
            </button>
          </div>
        </div>
      </header>

      {/* Contenido Principal */}
      <main className="flex-1 max-w-md w-full mx-auto p-4 flex flex-col justify-between">
        {modo === "chatbot" ? (
          /* MODO ASISTENTE CONVERSACIONAL (CHATBOT IA) */
          <div className="flex-1 flex flex-col bg-white rounded-3xl border border-slate-200/90 shadow-sm overflow-hidden min-h-[490px]">
            {/* Cabecera del Bot */}
            <div className="bg-gradient-to-r from-red-600 to-rose-700 text-white p-3.5 px-4 flex items-center justify-between shadow-xs">
              <div className="flex items-center gap-2.5">
                <div className="relative">
                  <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center text-lg">
                    🤖
                  </div>
                  <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-400 border-2 border-red-600 rounded-full"></span>
                </div>
                <div>
                  <h3 className="font-bold text-xs sm:text-sm leading-none">
                    Asistente Escolar IA
                  </h3>
                  <span className="text-[10px] text-red-100 flex items-center gap-1 mt-0.5">
                    <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    En línea • Exclusivo para Padres
                  </span>
                </div>
              </div>

              <span className="text-[10px] bg-white/20 font-semibold px-2 py-0.5 rounded-full">
                U.E. Fe y Alegría
              </span>
            </div>

            {/* Ventana de Mensajes */}
            <div className="flex-1 p-3.5 sm:p-4 overflow-y-auto space-y-3 bg-slate-50/70 text-xs sm:text-sm">
              {mensajes.map((m) => (
                <div
                  key={m.id}
                  className={`flex flex-col ${
                    m.sender === "user" ? "items-end" : "items-start"
                  }`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl p-3 shadow-2xs leading-relaxed ${
                      m.sender === "user"
                        ? "bg-red-600 text-white rounded-br-xs"
                        : "bg-white text-slate-800 border border-slate-200/80 rounded-bl-xs"
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{m.text}</div>
                  </div>

                  <span className="text-[9px] text-slate-400 mt-1 px-1">
                    {m.tiempo}
                  </span>

                  {/* Opciones interactivas */}
                  {m.opciones && m.opciones.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {m.opciones.map((op, opIdx) => (
                        <button
                          key={opIdx}
                          onClick={() => handleAccionBot(op.accion)}
                          className="text-[11px] font-semibold bg-white hover:bg-red-50 text-red-700 border border-red-200 rounded-full px-3 py-1 shadow-2xs transition active:scale-95"
                        >
                          {op.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {/* Typing indicator */}
              {typing && (
                <div className="flex items-center gap-1.5 bg-white p-2.5 px-4 rounded-2xl rounded-bl-xs border border-slate-200/80 w-fit text-slate-400 shadow-2xs">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-bounce"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-bounce delay-100"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-red-600 animate-bounce delay-200"></span>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Entrada Interactiva */}
            <div className="p-3 bg-white border-t border-slate-200/80">
              {fase === "identificador" && (
                <form onSubmit={handleEnviarIdentificador} className="flex gap-2">
                  <input
                    type="text"
                    value={identificador}
                    onChange={(e) => setIdentificador(e.target.value)}
                    placeholder="Escribe tu Carnet de Identidad (CI)..."
                    className="flex-1 bg-slate-100 border border-slate-300 rounded-2xl px-4 py-2.5 text-xs sm:text-sm focus:outline-none focus:border-red-500 focus:bg-white transition"
                    autoFocus
                    required
                  />
                  <button
                    type="submit"
                    disabled={!identificador.trim()}
                    className="w-10 h-10 rounded-2xl bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white flex items-center justify-center font-bold text-sm shadow-sm transition shrink-0"
                    title="Enviar"
                  >
                    ➔
                  </button>
                </form>
              )}

              {fase === "password" && (
                <form onSubmit={handleEnviarPassword} className="space-y-2">
                  <div className="relative flex items-center">
                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Escribe tu contraseña..."
                      className="w-full bg-slate-100 border border-slate-300 rounded-2xl pl-4 pr-20 py-2.5 text-xs sm:text-sm focus:outline-none focus:border-red-500 focus:bg-white transition"
                      autoFocus
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-12 text-[11px] font-semibold text-slate-500 hover:text-slate-800"
                    >
                      {showPassword ? "Ocultar" : "Ver"}
                    </button>
                    <button
                      type="submit"
                      disabled={!password.trim() || cargando}
                      className="absolute right-1.5 w-8 h-8 rounded-xl bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white flex items-center justify-center font-bold text-xs shadow-sm transition"
                      title="Ingresar"
                    >
                      {cargando ? "..." : "➔"}
                    </button>
                  </div>

                  <div className="flex items-center justify-between text-[11px] px-1">
                    <button
                      type="button"
                      onClick={() => handleAccionBot("reiniciar_identificador")}
                      className="text-slate-500 hover:text-slate-800"
                    >
                      ← Cambiar CI
                    </button>
                    <button
                      type="button"
                      onClick={() => handleAccionBot("ayuda_password")}
                      className="text-red-600 font-semibold hover:underline"
                    >
                      ¿Olvidaste tu contraseña?
                    </button>
                  </div>
                </form>
              )}

              {fase === "otp" && (
                <form onSubmit={handleEnviarOtp} className="space-y-2">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      maxLength={6}
                      value={codigoOtp}
                      onChange={(e) => setCodigoOtp(e.target.value.replace(/\D/g, ""))}
                      placeholder="Código de 6 dígitos"
                      className="flex-1 text-center font-mono tracking-widest text-base font-bold bg-slate-100 border border-slate-300 rounded-2xl px-4 py-2.5 focus:outline-none focus:border-red-500 focus:bg-white transition"
                      autoFocus
                      required
                    />
                    <button
                      type="submit"
                      disabled={codigoOtp.length < 6 || cargando}
                      className="px-4 py-2.5 rounded-2xl bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white font-bold text-xs transition"
                    >
                      {cargando ? "Validando..." : "Confirmar"}
                    </button>
                  </div>
                  <div className="text-center">
                    <button
                      type="button"
                      onClick={() => handleAccionBot("reenviar_otp")}
                      className="text-[11px] text-red-600 font-semibold hover:underline"
                    >
                      Reenviar código
                    </button>
                  </div>
                </form>
              )}

              {fase === "exito" && (
                <div className="py-2 text-center text-xs text-emerald-700 font-semibold flex items-center justify-center gap-1.5 animate-pulse">
                  <span>✓</span>
                  <span>Acceso verificado. Abriendo el portal de calificaciones...</span>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* MODO FORMULARIO TRADICIONAL */
          <div className="bg-white rounded-3xl border border-slate-200/90 p-6 shadow-sm space-y-4">
            <div className="text-center space-y-1">
              <div className="w-12 h-12 rounded-2xl bg-red-100 text-red-600 flex items-center justify-center text-2xl mx-auto mb-2">
                👨‍👩‍👧‍👦
              </div>
              <h2 className="text-lg font-black text-slate-900">Portal de Calificaciones</h2>
              <p className="text-xs text-slate-500">
                Ingresa con tu Carnet de Identidad y contraseña
              </p>
            </div>

            {formError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-xs">
                {formError}
              </div>
            )}

            <form onSubmit={handleTraditionalSubmit} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  Carnet de Identidad (CI):
                </label>
                <input
                  type="text"
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                  placeholder="Número de CI del tutor"
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-3 focus:outline-none focus:border-red-500 focus:bg-white text-sm transition"
                  required
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="font-bold text-slate-700">Contraseña:</label>
                  <button
                    type="button"
                    onClick={() => setInfoPasswordModal(true)}
                    className="text-red-600 font-semibold hover:underline text-[11px]"
                  >
                    ¿Olvidaste tu contraseña?
                  </button>
                </div>
                <input
                  type="password"
                  value={formPass}
                  onChange={(e) => setFormPass(e.target.value)}
                  placeholder="Tu contraseña personal"
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-3 focus:outline-none focus:border-red-500 focus:bg-white text-sm transition"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={formLoading}
                className="w-full py-3 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-bold rounded-xl text-sm shadow-md shadow-red-600/20 transition active:scale-98"
              >
                {formLoading ? "Ingresando..." : "Entrar al Portal"}
              </button>
            </form>

            <div className="pt-2 border-t border-slate-100 text-center">
              <button
                onClick={() => setModo("chatbot")}
                className="text-xs text-red-600 font-bold hover:underline flex items-center justify-center gap-1 mx-auto"
              >
                <span>🤖</span>
                <span>¿Prefieres ser guiado por el Asistente IA?</span>
              </button>
            </div>
          </div>
        )}

        {/* Modal informativo sobre olvido de contraseña en modo tradicional */}
        {infoPasswordModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4">
            <div className="bg-white rounded-2xl max-w-sm w-full p-5 shadow-xl space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <h4 className="font-bold text-slate-900 text-sm">
                  Restablecimiento de Contraseña
                </h4>
                <button
                  onClick={() => setInfoPasswordModal(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  ✕
                </button>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Por políticas de seguridad institucional de la U.E. Fe y Alegría, el restablecimiento de contraseñas de tutores se realiza de forma presencial en la <strong>Secretaría o Dirección del colegio</strong> presentando tu Carnet de Identidad (CI).
              </p>
              <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-[11px] text-slate-600">
                <strong>Horario de atención:</strong> Lunes a Viernes de 08:00 a 16:00.
              </div>
              <button
                onClick={() => setInfoPasswordModal(false)}
                className="w-full py-2 bg-red-600 text-white font-bold rounded-xl text-xs hover:bg-red-700 transition"
              >
                Entendido
              </button>
            </div>
          </div>
        )}

        {/* Pie con indicaciones institucionales */}
        <div className="mt-4 bg-white/70 backdrop-blur-sm rounded-2xl p-3 border border-slate-200/80 text-[11px] text-slate-500 text-center space-y-1">
          <p>
            <strong>Portal exclusivo para Padres de Familia</strong> • U.E. Fe y Alegría
          </p>
          <div className="text-slate-400">
            Acceso seguro y protegido a las calificaciones escolares
          </div>
        </div>
      </main>
    </div>
  );
}
