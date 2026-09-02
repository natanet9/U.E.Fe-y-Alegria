import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

vi.mock("../../src/services/gradesService", () => ({
  getGradesByCourse: vi.fn(),
}));

import { getGradesByCourse } from "../../src/services/gradesService";
import GradosPage from "../../src/pages/grados/GradosPage";

const mockGrados = [
  { id: 1, nombre: "1ro", total_estudiantes: 25, promedio_general: null },
  { id: 2, nombre: "2do", total_estudiantes: 30, promedio_general: 78.5 },
];

const mockResumen = [
  { titulo: "Total Cursos", valor: 8 },
  { titulo: "Total Grados", valor: 6 },
  { titulo: "Docentes Asignados", valor: 15 },
  { titulo: "Estudiantes Inscritos", valor: 180 },
];

describe("GradosPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getGradesByCourse.mockResolvedValue({
      grados: mockGrados,
      resumen: mockResumen,
    });
  });

  it("renderiza header y titulo", async () => {
    render(<GradosPage />);
    expect(await screen.findByRole("heading", { name: /grados/i })).toBeInTheDocument();
  });

  it("muestra grados desde API", async () => {
    render(<GradosPage />);
    expect(await screen.findByText("1ro")).toBeInTheDocument();
    expect(screen.getByText("2do")).toBeInTheDocument();
    expect(screen.getByText("25 estudiantes")).toBeInTheDocument();
    expect(screen.getByText("30 estudiantes")).toBeInTheDocument();
  });

  it("muestra resumen desde API", async () => {
    render(<GradosPage />);
    expect(await screen.findByText("Total Cursos")).toBeInTheDocument();
    expect(screen.getByText("Total Grados")).toBeInTheDocument();
    expect(screen.getByText("Docentes Asignados")).toBeInTheDocument();
    expect(screen.getByText("Estudiantes Inscritos")).toBeInTheDocument();
  });

  it("muestra estado vacio cuando no hay grados", async () => {
    getGradesByCourse.mockResolvedValue({ grados: [], resumen: [] });
    render(<GradosPage />);
    expect(await screen.findByText(/no hay grados para mostrar/i)).toBeInTheDocument();
  });

  it("no usa DEFAULT_GRADOS hardcodeados", async () => {
    render(<GradosPage />);
    await waitFor(() => expect(getGradesByCourse).toHaveBeenCalled());
    // Should not show default grade names that were hardcoded before
    // Pre-kinder, Kinder, 1ro de Primaria, etc. should only appear from API
    expect(screen.queryByText(/pre-kinder/i)).not.toBeInTheDocument();
  });

  it("muestra error cuando falla la carga", async () => {
    getGradesByCourse.mockRejectedValue({ response: { data: { error: "Error al cargar" } } });
    render(<GradosPage />);
    expect(await screen.findByText(/error al cargar/i)).toBeInTheDocument();
  });
});
