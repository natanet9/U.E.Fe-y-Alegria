import { describe, expect, it } from "vitest";
import {
  esConsultaFueraDeAlcance,
  procesarConsultaLogin,
  procesarConsultaPadres,
} from "../../../src/services/aiChatbotService";

describe("aiChatbotService - Limitaciones y Guardrails", () => {
  it("detecta operaciones matemáticas como 1+1 y consultas fuera de alcance", () => {
    expect(esConsultaFueraDeAlcance("1+1")).toBe(true);
    expect(esConsultaFueraDeAlcance("cuanto es 25 + 50")).toBe(true);
    expect(esConsultaFueraDeAlcance("calcula 10 * 8")).toBe(true);
    expect(esConsultaFueraDeAlcance("dime un chiste")).toBe(true);
    expect(esConsultaFueraDeAlcance("quien fue Simon Bolivar")).toBe(true);
    expect(esConsultaFueraDeAlcance("escribe codigo en python")).toBe(true);
  });

  it("permite consultas legítimas sobre notas y el colegio", () => {
    expect(esConsultaFueraDeAlcance("¿Cuáles son las notas de mi hijo?")).toBe(false);
    expect(esConsultaFueraDeAlcance("¿Tiene materias en riesgo o reprobadas?")).toBe(false);
    expect(esConsultaFueraDeAlcance("¿Cuánto tiene en Matemáticas?")).toBe(false);
    expect(esConsultaFueraDeAlcance("¿Cuántas faltas tiene este trimestre?")).toBe(false);
    expect(esConsultaFueraDeAlcance("¿Cómo descargo el boletín oficial?")).toBe(false);
  });

  it("rechaza consultas fuera de alcance en el login (ej: 1+1)", () => {
    const res = procesarConsultaLogin("1+1");
    expect(res.respuesta).toContain("Consulta fuera de alcance");
  });

  it("orienta sobre recuperación de contraseña en login indicando trámite presencial sin correo", () => {
    const res = procesarConsultaLogin("olvidé mi contraseña cómo la recupero");
    expect(res.respuesta).toContain("no se realiza recuperación automática por correo");
    expect(res.respuesta).toContain("Dirección o Secretaría");
    expect(res.respuesta).toContain("Cédula de Identidad (CI)");
  });

  it("explica que el usuario es el Carnet de Identidad (CI)", () => {
    const res = procesarConsultaLogin("¿cuál es mi usuario?");
    expect(res.respuesta).toContain("Carnet de Identidad (CI)");
  });
});

describe("aiChatbotService - Contexto Multihijo y Consultas Académicas", () => {
  const MOCK_CONTEXTO = {
    tutor: { nombre: "Carlos Mendoza", ci: "4829104" },
    estudiantes: [
      { id: 1, nombres: "Lucas", primer_apellido: "Mendoza", grado: "3ro Primaria A" },
      { id: 2, nombres: "Valentina", primer_apellido: "Mendoza", grado: "1ro Secundaria B" },
    ],
    estudianteActivo: { id: 1, nombres: "Lucas", primer_apellido: "Mendoza", grado: "3ro Primaria A" },
    todosBoletines: {
      1: {
        materias: [
          { area: "Matemática", promedio_final: 85, docente: "Prof. Gomez" },
          { area: "Ciencias Naturales", promedio_final: 48, docente: "Prof. Perez" },
        ],
        asistencias: [{ total: 40, presentes: 36, porcentaje: 90 }],
        observaciones: [
          { area: "Matemática", periodo: "1T", indicador: "EA", observacion: "Excelente participación." },
        ],
      },
      2: {
        materias: [
          { area: "Matemática", promedio_final: 92, docente: "Prof. Lopez" },
          { area: "Lenguaje", promedio_final: 88, docente: "Prof. Silva" },
        ],
        asistencias: [{ total: 40, presentes: 40, porcentaje: 100 }],
        observaciones: [],
      },
    },
  };

  it("rechaza operaciones matemáticas como 1+1 dentro del portal", () => {
    const res = procesarConsultaPadres("1+1", MOCK_CONTEXTO);
    expect(res.tipo).toBe("fuera_de_alcance");
    expect(res.respuesta).toContain("Consulta fuera de alcance");
  });

  it("genera un resumen comparativo cuando el tutor pregunta por 'mis hijos'", () => {
    const res = procesarConsultaPadres("¿Cómo van mis hijos?", MOCK_CONTEXTO);
    expect(res.tipo).toBe("resumen_multihijo");
    expect(res.respuesta).toContain("Lucas");
    expect(res.respuesta).toContain("Valentina");
    expect(res.respuesta).toContain("Ciencias Naturales"); // Materia en riesgo de Lucas
    expect(res.respuesta).toContain("Todas las materias aprobadas"); // Estado de Valentina
  });

  it("detecta al hijo por su nombre cuando se menciona en la consulta", () => {
    const res = procesarConsultaPadres("¿Cómo va Valentina en sus materias?", MOCK_CONTEXTO);
    expect(res.respuesta).toContain("Valentina");
  });

  it("identifica materias en riesgo (<51 pts)", () => {
    const res = procesarConsultaPadres("¿Tiene materias en riesgo o reprobadas?", MOCK_CONTEXTO);
    expect(res.tipo).toBe("materias_en_riesgo");
    expect(res.respuesta).toContain("Ciencias Naturales");
    expect(res.respuesta).toContain("48 pts");
  });

  it("responde sobre una materia específica (ej: Matemática)", () => {
    const res = procesarConsultaPadres("¿Cuál es la nota en Matemática de Lucas?", MOCK_CONTEXTO);
    expect(res.tipo).toBe("materia_detalle");
    expect(res.respuesta).toContain("Matemática");
    expect(res.respuesta).toContain("85 pts");
    expect(res.respuesta).toContain("Prof. Gomez");
  });

  it("responde sobre asistencia y faltas", () => {
    const res = procesarConsultaPadres("¿Cuántas faltas tiene Lucas?", MOCK_CONTEXTO);
    expect(res.tipo).toBe("asistencia");
    expect(res.respuesta).toContain("90% de presencia regular");
    expect(res.respuesta).toContain("Faltas acumuladas:");
  });

  it("explica el procedimiento para descargar el boletín oficial", () => {
    const res = procesarConsultaPadres("¿Cómo descargo el boletín?", MOCK_CONTEXTO);
    expect(res.tipo).toBe("descarga");
    expect(res.respuesta).toContain("Boletín Oficial");
  });
});
