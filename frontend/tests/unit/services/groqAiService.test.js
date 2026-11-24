import { describe, expect, it, beforeEach } from "vitest";
import {
  consultarAgenteIA,
  getGroqApiKey,
  hasGroqKey,
  GROQ_MODEL,
} from "../../../src/services/groqAiService";

describe("groqAiService - Agente IA con Groq", () => {
  const originalEnv = process.env.REACT_APP_GROQ_API_KEY;

  beforeEach(() => {
    process.env.REACT_APP_GROQ_API_KEY = "";
  });

  it("rechaza consultas fuera de alcance como 1+1 de inmediato por guardrail", async () => {
    const res = await consultarAgenteIA("1+1", {});
    expect(res.tipo).toBe("fuera_de_alcance");
    expect(res.fuente).toBe("guardrail");
    expect(res.respuesta).toContain("Consulta fuera de alcance");
  });

  it("utiliza el motor pedagógico local si no hay API key configurada en .env", async () => {
    process.env.REACT_APP_GROQ_API_KEY = "";
    const contexto = {
      tutor: { nombre: "Juan Perez" },
      estudiantes: [{ id: 1, nombres: "Mateo", primer_apellido: "Perez" }],
      estudianteActivo: { id: 1, nombres: "Mateo", primer_apellido: "Perez" },
      todosBoletines: { 1: { materias: [] } },
    };

    const res = await consultarAgenteIA("¿Cuáles son las materias de Mateo?", contexto);
    expect(res.fuente).toBe("local");
    expect(res.respuesta).toBeDefined();
  });

  it("obtiene correctamente la API key de process.env.REACT_APP_GROQ_API_KEY", () => {
    expect(hasGroqKey()).toBe(false);
    process.env.REACT_APP_GROQ_API_KEY = "'gsk_test1234567890abcdef1234567890'";
    expect(hasGroqKey()).toBe(true);
    expect(getGroqApiKey()).toBe("gsk_test1234567890abcdef1234567890");

    process.env.REACT_APP_GROQ_API_KEY = "";
    expect(hasGroqKey()).toBe(false);
  });
});
