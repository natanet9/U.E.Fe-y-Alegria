import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("../../src/services/studentsService", () => ({
  searchStudents: vi.fn(),
}));

vi.mock("../../src/services/periodoService", () => ({
  listPeriodos: vi.fn(),
}));

vi.mock("../../src/services/reportCardService", () => ({
  getReportCard: vi.fn(),
  downloadReportCard: vi.fn(),
}));

import { searchStudents } from "../../src/services/studentsService";
import { listPeriodos } from "../../src/services/periodoService";
import { getReportCard, downloadReportCard } from "../../src/services/reportCardService";
import ReportCardPage from "../../src/pages/reportes/ReportCardPage";

describe("ReportCardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renderiza header y buscador", () => {
    listPeriodos.mockResolvedValue({ periodos: [] });

    render(<ReportCardPage />);

    expect(screen.getByRole("heading", { name: /boletín de calificaciones/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/buscar por nombre, rude o ci/i)).toBeInTheDocument();
  });

  it("busca estudiantes y los muestra", async () => {
    listPeriodos.mockResolvedValue({ periodos: [] });
    searchStudents.mockResolvedValue({
      estudiantes: [{ id: 1, nombre: "Maria Lopez", rude: "R-001" }],
    });

    render(<ReportCardPage />);

    const input = screen.getByPlaceholderText(/buscar por nombre, rude o ci/i);
    await userEvent.type(input, "Maria");
    await userEvent.click(screen.getByRole("button", { name: /buscar/i }));

    await waitFor(() => expect(searchStudents).toHaveBeenCalledWith("Maria"));
    expect(await screen.findByText("Maria Lopez")).toBeInTheDocument();
  });

  it("selecciona estudiante", async () => {
    listPeriodos.mockResolvedValue({ periodos: [] });
    searchStudents.mockResolvedValue({
      estudiantes: [{ id: 1, nombre: "Maria Lopez", rude: "R-001" }],
    });

    render(<ReportCardPage />);

    const input = screen.getByPlaceholderText(/buscar por nombre, rude o ci/i);
    await userEvent.type(input, "Maria");
    await userEvent.click(screen.getByRole("button", { name: /buscar/i }));

    const studentBtn = await screen.findByText("Maria Lopez");
    await userEvent.click(studentBtn);

    expect(await screen.findByRole("heading", { name: /^Generar Boletín$/i })).toBeInTheDocument();
  });

  it("genera boletín (getReportCard)", async () => {
    listPeriodos.mockResolvedValue({ periodos: [{ id: 1, nombre: "2026", estado: "activo" }] });
    searchStudents.mockResolvedValue({
      estudiantes: [{ id: 1, nombre: "Maria Lopez", rude: "R-001" }],
    });
    getReportCard.mockResolvedValue({
      estudiante: "Maria Lopez",
      grado: "5to",
      rude: "R-001",
      materias: [],
      promedio_general: 85,
      asistencia: 95,
      estado: "Aprobado",
    });

    render(<ReportCardPage />);

    await waitFor(() => expect(listPeriodos).toHaveBeenCalled());

    const input = screen.getByPlaceholderText(/buscar por nombre, rude o ci/i);
    await userEvent.type(input, "Maria");
    await userEvent.click(screen.getByRole("button", { name: /buscar/i }));

    const studentBtn = await screen.findByText("Maria Lopez");
    await userEvent.click(studentBtn);

    await userEvent.click(screen.getByRole("button", { name: /generar boletín/i }));

    await waitFor(() => expect(getReportCard).toHaveBeenCalled());
    expect(await screen.findByRole("heading", { name: /^Boletín$/i })).toBeInTheDocument();
  });

  it("descarga PDF (downloadReportCard)", async () => {
    listPeriodos.mockResolvedValue({ periodos: [{ id: 1, nombre: "2026", estado: "activo" }] });
    searchStudents.mockResolvedValue({
      estudiantes: [{ id: 1, nombre: "Maria Lopez", rude: "R-001" }],
    });
    getReportCard.mockResolvedValue({
      estudiante: "Maria Lopez",
      grado: "5to",
      rude: "R-001",
      materias: [],
      promedio_general: 85,
      asistencia: 95,
      estado: "Aprobado",
    });
    downloadReportCard.mockResolvedValue({ data: new Blob() });

    render(<ReportCardPage />);

    await waitFor(() => expect(listPeriodos).toHaveBeenCalled());

    const input = screen.getByPlaceholderText(/buscar por nombre, rude o ci/i);
    await userEvent.type(input, "Maria");
    await userEvent.click(screen.getByRole("button", { name: /buscar/i }));

    const studentBtn = await screen.findByText("Maria Lopez");
    await userEvent.click(studentBtn);

    await userEvent.click(screen.getByRole("button", { name: /generar boletín/i }));
    await screen.findByRole("heading", { name: /^Boletín$/i });

    await userEvent.click(screen.getByRole("button", { name: /descargar pdf/i }));

    await waitFor(() => expect(downloadReportCard).toHaveBeenCalled());
  });
});
