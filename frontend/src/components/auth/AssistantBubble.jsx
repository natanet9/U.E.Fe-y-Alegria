import { useEffect, useRef, useState } from "react";
import "./AssistantBubble.css";
import apiClient from "../../services/apiClient";

const SUGGESTIONS = [
  "¿Qué información puedo consultar en el portal?",
  "¿Cómo son las inscripciones?",
  "¿Dónde consulto horarios y calendario?",
];

function AssistantBubble() {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      sender: "assistant",
      text: "¡Hola! Soy el asistente virtual de la U.E. Fe y Alegría. Puedo orientarte sobre información general de la institución y el portal.",
    },
  ]);
  const messagesRef = useRef(null);

  useEffect(() => {
    messagesRef.current?.scrollTo({
      top: messagesRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, pending]);

  const sendMessage = async (value = question) => {
    const text = value.trim();
    if (!text || pending) return;

    setQuestion("");
    setMessages((current) => [
      ...current,
      { id: `user-${Date.now()}`, sender: "user", text },
    ]);
    setPending(true);

    try {
      const history = messages
        .slice(-8)
        .map((message) => ({
          sender: message.sender === "user" ? "user" : "bot",
          text: message.text,
        }));
      const response = await apiClient.post("/assistant/chat/", {
        question: text,
        history,
      });
      const payload = response.data;
      if (!payload?.answer) {
        throw new Error("El servicio del asistente respondió sin contenido.");
      }
      setMessages((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          sender: "assistant",
          text: payload.answer,
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: `error-${Date.now()}`,
          sender: "assistant",
          text: error instanceof Error
            ? error.message
            : "No se pudo conectar con el asistente. Inténtalo nuevamente.",
          failed: true,
        },
      ]);
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="portal-assistant">
      {open && (
        <section
          className="portal-assistant-window"
          aria-label="Conversación con el asistente"
        >
          <header className="portal-assistant-title">
            <span>Conversa con nosotros</span>
            <button
              type="button"
              aria-label="Cerrar conversación"
              onClick={() => setOpen(false)}
            >
              ×
            </button>
          </header>
          <div className="portal-assistant-chat">
            <header className="portal-assistant-chat-header">
              <span className="portal-assistant-avatar" aria-hidden="true">✦</span>
              <span className="portal-assistant-heading">
                <strong>Asistente virtual</strong>
                <small><i /> Disponible para ayudarte</small>
              </span>
              <span className="portal-assistant-label">Fe y Alegría</span>
            </header>

            <div className="portal-assistant-messages" ref={messagesRef} aria-live="polite">
              {messages.map((message, index) => (
                <article
                  className={`portal-assistant-message ${message.sender}${message.failed ? " failed" : ""}`}
                  key={message.id}
                >
                  {message.sender === "assistant" && (
                    <span className="portal-assistant-message-avatar" aria-hidden="true">✦</span>
                  )}
                  <div className="portal-assistant-message-content">{message.text}</div>
                  {index === 0 && messages.length === 1 && (
                    <div className="portal-assistant-suggestions" aria-label="Preguntas sugeridas">
                      {SUGGESTIONS.map((suggestion) => (
                        <button
                          key={suggestion}
                          type="button"
                          onClick={() => sendMessage(suggestion)}
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  )}
                </article>
              ))}
              {pending && (
                <div className="portal-assistant-typing" role="status">
                  <i /><i /><i /><span>Escribiendo...</span>
                </div>
              )}
            </div>

            <form
              className="portal-assistant-composer"
              onSubmit={(event) => {
                event.preventDefault();
                sendMessage();
              }}
            >
              <label className="portal-assistant-visually-hidden" htmlFor="portal-assistant-input">
                Escribe tu pregunta
              </label>
              <textarea
                id="portal-assistant-input"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    sendMessage();
                  }
                }}
                placeholder="Escribe tu pregunta..."
                maxLength={2000}
                rows={1}
              />
              <button type="submit" disabled={!question.trim() || pending} aria-label="Enviar mensaje">
                ↑
              </button>
            </form>
          </div>
        </section>
      )}
      <button
        className={`portal-assistant-launcher${open ? " is-open" : ""}`}
        type="button"
        aria-label={open ? "Cerrar asistente virtual" : "Abrir asistente virtual"}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <span aria-hidden="true">{open ? "×" : "✦"}</span>
      </button>
    </div>
  );
}

export default AssistantBubble;
