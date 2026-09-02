import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("../../src/services/reportsService", () => ({
  getReportsPage: vi.fn(),
  getReportsExportHistory: vi.fn(),
  downloadReportsDocument: vi.fn(),
}));

vi.mock("../../src/services/periodoService", () => ({
  listPeriodos: vi.fn(),
  markPeriodoEnviado: vi.fn(),
}));

import { getReportsPage, getReportsExportHistory, downloadReportsDocument } from "../../src/services/reportsService";
import { listPeriodos, markPeriodoEnviado } from "../../src/services/periodoService";
import ReportesPage from "../../src/pages/reportes/ReportesPage";

const mockResumen = [
  { titulo: "Estudiantes", valor: 150, detalle: "Inscritos activos", acento: "blue" },
  { titulo: "Docentes", valor: 12, detalle: "Con asignaciones", acento: "violet" },
  { titulo: "Cursos", valor: 8, detalle: "Activos", acento: "green" },
  { titulo: "Asignaciones", valor: 20, detalle: "Docente-Área-Curso", acento: "orange" },
];

describe("ReportesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    listPeriodos.mockResolvedValue({ periodos: [] });
    getReportsPage.mockResolvedValue({ resumen: mockResumen });
    getReportsExportHistory.mockResolvedValue({ exports: [] });
  });

  it("renderiza header y titulo", async () => {
    render(<ReportesPage />);
    expect(await screen.findByRole("heading", { name: /reportes/i })).toBeInTheDocument();
  });

  it("muestra stat cards desde API", async () => {
    render(<ReportesPage />);
    expect(await screen.findByText("Estudiantes")).toBeInTheDocument();
    expect(screen.getByText("150")).toBeInTheDocument();
    expect(screen.getByText("Docentes")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("Cursos")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
  });

  it("muestra historial de exportaciones vacio", async () => {
    render(<ReportesPage />);
    expect(await screen.findByText(/aún no hay exportaciones/i)).toBeInTheDocument();
  });

  it("muestra exportaciones del historial", async () => {
    getReportsExportHistory.mockResolvedValue({
      exports: [
        { id: 1, formato: "xlsx", periodo: "T1 2026", usuario: "Admin", creado_en: "2026-03-01", gestion: "2026" },
      ],
    });
    render(<ReportesPage />);
    expect(await screen.findByText(/xlsx/i)).toBeInTheDocument();
    expect(screen.getByText(/admin/i)).toBeInTheDocument();
  });

  it("muestra error cuando falla la carga", async () => {
    getReportsPage.mockRejectedValue({ response: { data: { error: "Error de carga" } } });
    render(<ReportesPage />);
    expect(await screen.findByText(/error de carga/i)).toBeInTheDocument();
  });

  it("no tiene secciones hardcodeadas (solo usa API)", async () => {
    render(<ReportesPage />);
    await waitFor(() => expect(getReportsPage).toHaveBeenCalled());
    // Should not contain any hardcoded chart section text
    expect(screen.queryByText(/tendencia de calificaciones/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/crecimiento de estudiantes/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/distribución de rendimiento/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/asistencia por grado/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/ranking de materias/i)).not.toBeInTheDocument();
  });

  it("descarga informe", async () => {
    downloadReportsDocument.mockResolvedValue({
      data: new Blob(),
      headers: { "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document" },
    });
    render(<ReportesPage />);
    await screen.findByText("Estudiantes");
    await userEvent.click(screen.getByRole("button", { name: /descargar informe/i }));
    await waitFor(() => expect(downloadReportsDocument).toHaveBeenCalled());
  });
});
