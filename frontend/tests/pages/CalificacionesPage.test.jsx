import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("../../src/services/gradesService", () => ({
  getGradesPage: vi.fn(),
}));

import { getGradesPage } from "../../src/services/gradesService";
import CalificacionesPage from "../../src/pages/calificaciones/CalificacionesPage";

const mockApiResponse = {
  resumen: [
    { titulo: "Estudiantes", valor: 150, detalle: "Inscritos activos", acento: "blue" },
    { titulo: "Promedio General", valor: 76.5, detalle: "Periodo activo", acento: "green" },
  ],
  filtros: {
    materias: ["Matemáticas", "Lenguaje", "Ciencias"],
    periodos: [{ id: 1, nombre: "T1 2026" }],
  },
  promedio_por_asignatura: {
    labels: ["Matemáticas", "Lenguaje", "Ciencias"],
    data: [80, 75, 70],
  },
  mejores_estudiantes: [
    { id: 1, posicion: 1, nombre: "Juan Perez", documento: "12345", promedio: 95, detalle: "Excelente rendimiento" },
  ],
  por_estudiante: [
    {
      id: 1, estudiante: "Juan Perez", documento: "12345",
      materias: { "Matemáticas": 90, "Lenguaje": 85 },
      promedio: 87.5, tendencia: "up", asistencia: 95,
    },
  ],
  por_curso: [
    { id: 1, curso: "1ro A", promedio: 82, estudiantes: 25, mejor_estudiante: "Juan Perez", distribucion: [] },
  ],
  permisos: { puede_crear: false, puede_ver_todo: true },
  paginacion: { pagina: 1, paginas: 1, anterior: false, siguiente: false, total: 1 },
};

describe("CalificacionesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getGradesPage.mockResolvedValue(mockApiResponse);
  });

  it("renderiza header y titulo", async () => {
    render(<CalificacionesPage />);
    expect(await screen.findByRole("heading", { name: /calificaciones/i }, { timeout: 5000 })).toBeInTheDocument();
  });

  it("muestra stat cards desde API", async () => {
    render(<CalificacionesPage />);
    const cards = await screen.findAllByText("Estudiantes", undefined, { timeout: 5000 });
    expect(cards.length).toBeGreaterThanOrEqual(1);
    expect(await screen.findByText("150", undefined, { timeout: 5000 })).toBeInTheDocument();
    const promCards = await screen.findAllByText("Promedio General", undefined, { timeout: 5000 });
    expect(promCards.length).toBeGreaterThanOrEqual(1);
    expect(await screen.findByText("76.5", undefined, { timeout: 5000 })).toBeInTheDocument();
  });

  it("muestra materias desde API en tabla", async () => {
    render(<CalificacionesPage />);
    expect(await screen.findByText("Matemáticas", undefined, { timeout: 5000 })).toBeInTheDocument();
    expect(await screen.findByText("Lenguaje", undefined, { timeout: 5000 })).toBeInTheDocument();
    expect(await screen.findByText("Ciencias", undefined, { timeout: 5000 })).toBeInTheDocument();
  });

  it("no usa nombres de materias hardcodeadas como fallback", async () => {
    render(<CalificacionesPage />);
    await screen.findByText("Calificaciones", undefined, { timeout: 5000 });
    expect(screen.queryByText(/Historia/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Inglés/i)).not.toBeInTheDocument();
  });

  it("muestra mejores estudiantes", async () => {
    render(<CalificacionesPage />);
    expect(await screen.findByText("Juan Perez", undefined, { timeout: 5000 })).toBeInTheDocument();
    expect(await screen.findByText("95", undefined, { timeout: 5000 })).toBeInTheDocument();
  });

  it("muestra estado vacio en tabla cuando no hay estudiantes", async () => {
    getGradesPage.mockResolvedValue({
      ...mockApiResponse,
      por_estudiante: [],
      calificaciones: [],
      filtros: { ...mockApiResponse.filtros, materias: ["Matemáticas"] },
    });
    render(<CalificacionesPage />);
    await screen.findByText("Calificaciones", undefined, { timeout: 5000 });

    await userEvent.click(screen.getByRole("button", { name: /por estudiante/i }));
    expect(await screen.findByText(/no se encontraron calificaciones/i, undefined, { timeout: 5000 })).toBeInTheDocument();
  });

  it("no contiene PieChart hardcodeado", async () => {
    render(<CalificacionesPage />);
    await screen.findByText("Calificaciones", undefined, { timeout: 5000 });
    expect(screen.queryByText(/excelente/i)).not.toBeInTheDocument();
  });

  it("cambia de pestana correctamente", async () => {
    render(<CalificacionesPage />);
    await screen.findByText("Resumen", undefined, { timeout: 5000 });

    await userEvent.click(screen.getByRole("button", { name: /por curso/i }));
    expect(await screen.findByText(/1ro a/i, undefined, { timeout: 5000 })).toBeInTheDocument();
  });

  it("muestra error cuando falla la carga", async () => {
    getGradesPage.mockRejectedValue({ response: { data: { error: "Error de carga" } } });
    render(<CalificacionesPage />);
    expect(await screen.findByText(/error de carga/i, undefined, { timeout: 5000 })).toBeInTheDocument();
  });
});
