import { useEffect, useRef, useState } from "react";

const API_URL = import.meta.env.VITE_ASSISTANT_API_URL || "http://127.0.0.1:8001";
const getPortalContext = () =>
  window.FEYA_ASSISTANT_CONTEXT || {
    tutor: { nombre_completo: "Tutor de la U.E. Fe y Alegría" },
    estudiantes: [],
    todosBoletines: {},
  };

const INITIAL_MESSAGES = [
  {
    id: "welcome",
    sender: "bot",
    text: "Hola, soy el Asistente Pedagógico de Fe y Alegría. ¿En qué puedo orientarte?",
  },
];

export default function App() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [pending, setPending] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  const send = async (question = input) => {
    const text = question.trim();
    if (!text || pending) return;

    setInput("");
    setMessages((current) => [
      ...current,
      { id: `user-${Date.now()}`, sender: "user", text },
    ]);
    setPending(true);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: text,
          context: getPortalContext(),
          history: messages,
        }),
      });
      if (!response.ok) throw new Error("El asistente no está disponible.");
      const data = await response.json();
      setMessages((current) => [
        ...current,
        {
          id: `bot-${Date.now()}`,
          sender: "bot",
          text: data.answer,
          source: data.source,
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: `error-${Date.now()}`,
          sender: "bot",
          text: error.message || "No se pudo procesar la consulta.",
        },
      ]);
    } finally {
      setPending(false);
    }
  };

  return (
    <>
      <button
        className="assistant-launcher"
        type="button"
        aria-label="Abrir asistente pedagógico"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <span aria-hidden="true">✦</span>
      </button>

      {open && (
        <section className="assistant-panel" aria-label="Asistente pedagógico">
          <header className="assistant-header">
            <div className="assistant-avatar" aria-hidden="true">🤖</div>
            <div>
              <strong>Asistente Pedagógico IA</strong>
              <small>U.E. Fe y Alegría · Familias</small>
            </div>
            <button
              type="button"
              aria-label="Cerrar asistente"
              onClick={() => setOpen(false)}
            >
              ×
            </button>
          </header>

          <div className="assistant-messages" aria-live="polite">
            {messages.map((message) => (
              <article
                key={message.id}
                className={`assistant-message ${message.sender}`}
              >
                <div>{message.text}</div>
                {message.source === "groq" && (
                  <small>Respuesta generada con Groq</small>
                )}
              </article>
            ))}
            {pending && (
              <article className="assistant-message bot">
                <div className="typing">
                  <i /><i /><i />
                  <span>Analizando consulta...</span>
                </div>
              </article>
            )}
            <div ref={endRef} />
          </div>

          <form
            className="assistant-composer"
            onSubmit={(event) => {
              event.preventDefault();
              send();
            }}
          >
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Pregunta sobre notas, asistencia o estudio..."
              maxLength={2000}
            />
            <button type="submit" disabled={!input.trim() || pending}>➔</button>
          </form>
        </section>
      )}
    </>
  );
}
