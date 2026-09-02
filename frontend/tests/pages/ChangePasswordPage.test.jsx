import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import ChangePasswordPage from "../../src/pages/auth/ChangePasswordPage";

describe("ChangePasswordPage", () => {
  it("muestra el formulario de cambio de contraseña", () => {
    render(<ChangePasswordPage />);

    expect(screen.getByText(/cambiar contraseña/i)).toBeInTheDocument();
    expect(screen.getByText(/ingresa tu contraseña actual y la nueva/i)).toBeInTheDocument();
  });
});