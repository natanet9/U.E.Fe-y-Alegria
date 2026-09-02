import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
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

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getStoredUser.mockReturnValue({ nombre: "Ana", apellido: "Perez" });
  });

  it("renderiza el dashboard con datos", async () => {
    getCurrentUser.mockResolvedValue({ nombre: "Ana", apellido: "Perez" });
    getDashboardCards.mockResolvedValue({
      stats: { total_estudiantes: 10, total_docentes: 3, total_asignaciones: 5, periodos_activos: 1 },
      licencias_pendientes: 2,
      periodo_activo: { nombre: "T1", gestion: 2026 },
    });
    getDashboardData.mockResolvedValue({
      stats: {
        total_estudiantes: 10,
        total_docentes: 3,
        total_asignaciones: 5,
        periodos_activos: 1,
      },
      alertas: [{ tipo: "warning", mensaje: "1 docentes aun no registran notas en el periodo activo" }],
      licencias_pendientes: 2,
      asistencia_semanal: { labels: ["22/05"], data: [80] },
      promedio_por_asignatura: { labels: ["Ciencias"], data: [88] },
      rendimiento: [
        { label: "Excelente", value: 50, color: "#10b981", description: "90-100 puntos" },
        { label: "Muy Bueno", value: 25, color: "#3b82f6", description: "80-89 puntos" },
        { label: "Bueno", value: 15, color: "#f59e0b", description: "70-79 puntos" },
        { label: "Suficiente", value: 5, color: "#f97316", description: "61-69 puntos" },
        { label: "Reprobado", value: 5, color: "#ef4444", description: "Menos de 61 puntos" },
      ],
      estudiantes_destacados: [{ nombre: "Juan Perez", promedio: 94.5, mensaje: "Promedio acumulado en T1 2026" }],
      estudiantes_con_notas: 2,
      ultimos_usuarios: [
        { nombre_completo: "Ana Perez", email: "ana@test.com", updated_at: "2026-05-28 10:00:00" },
      ],
      periodo_activo: { nombre: "T1", gestion: 2026 },
    });

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/bienvenido, ana/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /alertas/i })).toBeInTheDocument();
    expect(screen.getByText(/total estudiantes/i)).toBeInTheDocument();
    expect(screen.getByText(/^10$/)).toBeInTheDocument();
    expect(screen.getByText(/1 docentes aun no registran notas/i)).toBeInTheDocument();
    expect(screen.getByText(/2 licencias pendientes/i)).toBeInTheDocument();
    expect(screen.getByText(/ciencias/i)).toBeInTheDocument();
    expect(screen.getByText(/juan perez/i)).toBeInTheDocument();
  });

  it("muestra error cuando falla la carga", async () => {
    getCurrentUser.mockResolvedValue({ nombre: "Ana", apellido: "Perez" });
    getDashboardCards.mockResolvedValue({
      stats: { total_estudiantes: 0, total_docentes: 0, total_asignaciones: 0, periodos_activos: 0 },
      licencias_pendientes: 0,
      periodo_activo: null,
    });
    getDashboardData.mockRejectedValue({ response: { data: { error: "No fue posible cargar el dashboard" } } });

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/no fue posible cargar el dashboard/i)).toBeInTheDocument();
  });
});