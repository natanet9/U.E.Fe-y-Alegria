import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("../../../src/services/authService", () => ({
  getStoredUser: vi.fn(),
  logoutRequest: vi.fn(),
}));

import { getStoredUser, logoutRequest } from "../../../src/services/authService";
import PanelAcademicoLayout from "../../../src/layouts/PanelAcademicoLayout";

describe("PanelAcademicoLayout", () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    vi.clearAllMocks();
  });

  it("muestra el menu de director y el contenido del outlet", () => {
    getStoredUser.mockReturnValue({ nombre: "Ana", primer_apellido: "Perez", cargo: "director" });

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route
            element={<PanelAcademicoLayout />}
          >
            <Route path="/dashboard" element={<div>contenido dashboard</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText(/contenido dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/ana perez/i)).toBeInTheDocument();
    expect(screen.getByText(/panel del director/i)).toBeInTheDocument();
    expect(screen.getByText(/docentes/i)).toBeInTheDocument();
    expect(screen.getByText(/periodos/i)).toBeInTheDocument();
    expect(screen.getByText(/licencias/i)).toBeInTheDocument();
  });

  it("muestra menu completo para director", () => {
    getStoredUser.mockReturnValue({ nombre: "Carlos", primer_apellido: "Mendoza", cargo: "director" });

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route element={<PanelAcademicoLayout />}>
            <Route path="/dashboard" element={<div>contenido dashboard</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText(/panel del director/i)).toBeInTheDocument();
    expect(screen.getByText(/boletín/i)).toBeInTheDocument();
    expect(screen.getByText(/licencias/i)).toBeInTheDocument();
  });

  it("oculta items segun rol de docente", () => {
    getStoredUser.mockReturnValue({ nombre: "Pedro", primer_apellido: "Garcia", cargo: "docente" });

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route element={<PanelAcademicoLayout />}>
            <Route path="/dashboard" element={<div>contenido dashboard</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText(/docentes/i)).toBeInTheDocument();
    expect(screen.getByText(/boletín/i)).toBeInTheDocument();
    expect(screen.queryByText(/catálogos/i)).not.toBeInTheDocument();
  });

  it("ejecuta logout desde el menu del usuario", async () => {
    getStoredUser.mockReturnValue({ nombre: "Ana", primer_apellido: "Perez", cargo: "docente" });
    logoutRequest.mockResolvedValue(undefined);

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route
            element={<PanelAcademicoLayout />}
          >
            <Route path="/dashboard" element={<div>contenido dashboard</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    await userEvent.click(screen.getByText(/ana perez/i));
    await userEvent.click(screen.getByText(/cerrar sesión/i));

    expect(logoutRequest).toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith("/login");
  });
});