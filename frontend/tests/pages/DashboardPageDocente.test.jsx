import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("../../src/services/dashboardService", () => ({
  getDashboardData: vi.fn(),
  getDashboardCards: vi.fn(),
}));

vi.mock("../../src/services/authService", () => ({
  getCurrentUser: vi.fn(),
  getStoredUser: vi.fn(),
}));

import { getDashboardData, getDashboardCards } from "../../src/services/dashboardService";
import { getCurrentUser, getStoredUser } from "../../src/services/authService";
import DashboardPage from "../../src/pages/dashboard/DashboardPage";

const mockAsignaciones = [
  {
    id: 1,
    curso: "3 A",
    area: "Matemáticas",
    gestion: 2026,
    total_estudiantes: 30,
    estudiantes_con_notas: 25,
    actividades_count: 8,
    completitud: 83,
    cerrado: false,
  },
  {
    id: 2,
    curso: "3 B",
    area: "Matemáticas",
    gestion: 2026,
    total_estudiantes: 28,
    estudiantes_con_notas: 28,
    actividades_count: 8,
    completitud: 100,
    cerrado: true,
  },
  {
    id: 3,
    curso: "4 A",
    area: "Ciencias",
    gestion: 2026,
    total_estudiantes: 32,
    estudiantes_con_notas: 10,
    actividades_count: 5,
    completitud: 31,
    cerrado: false,
  },
];

describe("DashboardPage - Docente View", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getStoredUser.mockReturnValue({ nombre: "Carlos", apellido: "Mendoza", cargo: "docente" });
  });

  it("muestra la sección de asignaciones con todos los detalles", async () => {
    getCurrentUser.mockResolvedValue({ nombre: "Carlos", apellido: "Mendoza", cargo: "docente" });
    getDashboardCards.mockResolvedValue({
      stats: { total_estudiantes: 0, total_docentes: 0, total_asignaciones: 3, periodos_activos: 1 },
      licencias_pendientes: 0,
      periodo_activo: { nombre: "T1", gestion: 2026 },
    });
    getDashboardData.mockResolvedValue({
      stats: { total_estudiantes: 0, total_docentes: 0, total_asignaciones: 3, periodos_activos: 1 },
      alertas: [],
      licencias_pendientes: 0,
      promedio_por_asignatura: { labels: [], data: [] },
      rendimiento: [],
      estudiantes_destacados: [],
      estudiantes_con_notas: 0,
      ultimos_usuarios: [],
      periodo_activo: { nombre: "T1", gestion: 2026, id: 1 },
      asignaciones: mockAsignaciones,
    });

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/bienvenido, carlos/i)).toBeInTheDocument();

    const asignaciones = screen.getByRole("heading", { name: /mis asignaciones/i });
    expect(asignaciones).toBeInTheDocument();

    expect(screen.getByText("3 A")).toBeInTheDocument();
    expect(screen.getByText("3 B")).toBeInTheDocument();
    expect(screen.getByText("4 A")).toBeInTheDocument();

    expect(screen.getAllByText("Matemáticas").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Ciencias")).toBeInTheDocument();

    expect(screen.getByText("83%")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
    expect(screen.getByText("31%")).toBeInTheDocument();

    expect(screen.getAllByText("Abierto").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Cerrado")).toBeInTheDocument();

    expect(screen.getAllByText(/t1 2026/i).length).toBeGreaterThanOrEqual(2);
  });

  it("no muestra la sección de asignaciones cuando el array está vacío", async () => {
    getCurrentUser.mockResolvedValue({ nombre: "Carlos", apellido: "Mendoza", cargo: "docente" });
    getDashboardCards.mockResolvedValue({
      stats: { total_estudiantes: 0, total_docentes: 0, total_asignaciones: 0, periodos_activos: 1 },
      licencias_pendientes: 0,
      periodo_activo: { nombre: "T1", gestion: 2026 },
    });
    getDashboardData.mockResolvedValue({
      stats: { total_estudiantes: 0, total_docentes: 0, total_asignaciones: 0, periodos_activos: 1 },
      alertas: [],
      licencias_pendientes: 0,
      promedio_por_asignatura: { labels: [], data: [] },
      rendimiento: [],
      estudiantes_destacados: [],
      estudiantes_con_notas: 0,
      ultimos_usuarios: [],
      periodo_activo: { nombre: "T1", gestion: 2026 },
      asignaciones: [],
    });

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/bienvenido, carlos/i)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /mis asignaciones/i })).not.toBeInTheDocument();
  });

  it("muestra el loading state inicialmente", async () => {
    let resolveCards, resolveData;
    getDashboardCards.mockReturnValue(new Promise((res) => { resolveCards = res; }));
    getDashboardData.mockReturnValue(new Promise((res) => { resolveData = res; }));
    getCurrentUser.mockResolvedValue({ nombre: "Carlos", apellido: "Mendoza", cargo: "docente" });

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(screen.getByText(/bienvenido, carlos/i)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /mis asignaciones/i })).not.toBeInTheDocument();

    resolveCards({
      stats: { total_estudiantes: 0, total_docentes: 0, total_asignaciones: 0, periodos_activos: 1 },
      licencias_pendientes: 0,
      periodo_activo: { nombre: "T1", gestion: 2026 },
    });

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: /mis asignaciones/i })).not.toBeInTheDocument();
    });

    resolveData({
      stats: { total_estudiantes: 0, total_docentes: 0, total_asignaciones: 0, periodos_activos: 1 },
      alertas: [],
      licencias_pendientes: 0,
      promedio_por_asignatura: { labels: [], data: [] },
      rendimiento: [],
      estudiantes_destacados: [],
      estudiantes_con_notas: 0,
      ultimos_usuarios: [],
      periodo_activo: { nombre: "T1", gestion: 2026 },
      asignaciones: [mockAsignaciones[0]],
    });

    expect(await screen.findByRole("heading", { name: /mis asignaciones/i })).toBeInTheDocument();
  });
});
