import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("../../src/services/catalogosService", () => ({
  getCatalogos: vi.fn(),
  deleteCatalogo: vi.fn(),
}));

vi.mock("../../src/hooks/useDialog", () => ({
  useDialog: () => ({
    dialog: { isOpen: false, mode: "confirm", message: "", iconType: "info", title: "", inputPlaceholder: "", inputValue: "" },
    confirm: vi.fn().mockResolvedValue(true),
    prompt: vi.fn().mockResolvedValue("test"),
    handleConfirm: vi.fn(),
    handleCancel: vi.fn(),
  }),
}));

import { getCatalogos, deleteCatalogo } from "../../src/services/catalogosService";
import CatalogosPage from "../../src/pages/catalogos/CatalogosPage";

describe("CatalogosPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // default resolved value to avoid undefined.then in component
    getCatalogos.mockResolvedValue({ niveles: [], grados: [], paralelos: [], areas: [], dimensiones: [] });
  });

  it("renderiza con tabs (Niveles, Grados, Paralelos, Áreas, Dimensiones)", () => {
    render(<CatalogosPage />);

    expect(screen.getByRole("button", { name: "Niveles" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Grados" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Paralelos" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Áreas" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Dimensiones" })).toBeInTheDocument();
  });

  it("carga datos y muestra items", async () => {
    getCatalogos.mockResolvedValue({
      niveles: [{ id: 1, nombre: "Primaria" }],
      grados: [],
      paralelos: [],
      areas: [],
      dimensiones: [],
    });

    render(<CatalogosPage />);

    expect(await screen.findByText("Primaria")).toBeInTheDocument();
    await waitFor(() => expect(getCatalogos).toHaveBeenCalledWith("niveles"));
  });

  it("llama a deleteCatalogo al confirmar eliminación", async () => {
    deleteCatalogo.mockResolvedValue({});
    getCatalogos.mockResolvedValue({
      niveles: [{ id: 1, nombre: "Primaria" }],
      grados: [],
      paralelos: [],
      areas: [],
      dimensiones: [],
    });

    render(<CatalogosPage />);

    const deleteBtn = await screen.findByRole("button", { name: /eliminar/i });
    await userEvent.click(deleteBtn);

    await waitFor(() => expect(deleteCatalogo).toHaveBeenCalledWith("niveles", 1));
  });
});
