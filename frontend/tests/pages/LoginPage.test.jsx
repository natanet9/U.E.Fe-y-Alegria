import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import LoginPage from "../../src/pages/auth/LoginPage";

describe("LoginPage", () => {
  it("renderiza el contenido de autenticacion", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    expect(screen.getByText(/sistema academico/i)).toBeInTheDocument();
    expect(screen.getByText(/bienvenido/i)).toBeInTheDocument();
    expect(screen.getByText(/copyright 2026 u.e.panama/i)).toBeInTheDocument();
  });
});