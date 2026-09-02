import { beforeEach, describe, expect, it, vi } from "vitest";
import { act } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("../../../src/services/authService", () => ({
  loginRequest: vi.fn(),
}));

import { loginRequest } from "../../../src/services/authService";
import LoginForm from "../../../src/components/auth/LoginForm";

describe("LoginForm", () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    vi.clearAllMocks();
  });

  it("inicia sesion y navega al dashboard", async () => {
    loginRequest.mockResolvedValue({ id: "u-1" });

    render(<LoginForm />);

    await act(async () => {
      await userEvent.type(screen.getByLabelText(/correo electronico/i), "ana@test.com");
      await userEvent.type(screen.getByLabelText(/contrasena/i), "Secret123!");
      await userEvent.click(screen.getByRole("button", { name: /iniciar sesion/i }));
    });

    expect(loginRequest).toHaveBeenCalledWith("ana@test.com", "Secret123!");
    expect(mockNavigate).toHaveBeenCalledWith("/dashboard");
  });

  it("muestra error cuando el login falla", async () => {
    loginRequest.mockRejectedValue({ response: { data: { error: "Credenciales invalidas" } } });

    render(<LoginForm />);

    await act(async () => {
      await userEvent.type(screen.getByLabelText(/correo electronico/i), "ana@test.com");
      await userEvent.type(screen.getByLabelText(/contrasena/i), "bad-pass");
      await userEvent.click(screen.getByRole("button", { name: /iniciar sesion/i }));
    });

    expect(await screen.findByText(/credenciales invalidas/i)).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});