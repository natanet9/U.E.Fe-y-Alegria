import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("../../src/services/periodoService", () => ({
  listPeriodos: vi.fn(),
  createPeriodo: vi.fn(),
  updatePeriodo: vi.fn(),
  deletePeriodo: vi.fn(),
  habilitarPeriodo: vi.fn(),
  cerrarPeriodo: vi.fn(),
  markPeriodoEnviado: vi.fn(),
}));

vi.mock("../../src/services/licenciasService", () => ({
  getLicenciasPage: vi.fn(),
  approveLicencia: vi.fn(),
  getLicenciaDetail: vi.fn(),
}));

import { listPeriodos, createPeriodo } from "../../src/services/periodoService";
import { getLicenciasPage, approveLicencia } from "../../src/services/licenciasService";
import PeriodosPage from "../../src/pages/director/PeriodosPage";
import LicenciasPage from "../../src/pages/director/LicenciasPage";

describe("director pages", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("carga la página de periodos", async () => {
    listPeriodos.mockResolvedValue({ periodos: [] });

    render(<PeriodosPage />);

    expect(await screen.findByRole("heading", { name: /periodos/i })).toBeInTheDocument();
    await waitFor(() => expect(listPeriodos).toHaveBeenCalled());
  });

  it("crea un periodo desde el formulario", async () => {
    listPeriodos.mockResolvedValue({ periodos: [] });
    createPeriodo.mockResolvedValue({});

    render(<PeriodosPage />);

    await waitFor(() => expect(screen.getByRole("button", { name: /crear periodo/i })).toBeInTheDocument());
    await userEvent.type(screen.getByLabelText(/nombre/i), "Primer trimestre");
    await userEvent.type(screen.getAllByLabelText(/^gestión$/i)[1], "2026");
    await userEvent.click(screen.getByRole("button", { name: /crear periodo/i }));

    await waitFor(() => expect(createPeriodo).toHaveBeenCalled());
  });

  it("carga la página de licencias", async () => {
    getLicenciasPage.mockResolvedValue({ licencias: { items: [], pagina: 1, paginas: 1 } });

    render(<LicenciasPage />);

    expect(await screen.findByRole("heading", { name: /licencias/i })).toBeInTheDocument();
    await waitFor(() => expect(getLicenciasPage).toHaveBeenCalled());
  });
});
