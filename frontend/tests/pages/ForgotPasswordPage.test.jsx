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

vi.mock("../../src/services/authService", () => ({
  forgotPasswordRequest: vi.fn(),
  verifyResetCodeRequest: vi.fn(),
  resetPasswordRequest: vi.fn(),
}));

import {
  forgotPasswordRequest,
  resetPasswordRequest,
  verifyResetCodeRequest,
} from "../../src/services/authService";
import ForgotPasswordPage from "../../src/pages/auth/ForgotPasswordPage";

describe("ForgotPasswordPage", () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    vi.clearAllMocks();
  });

  it("envia el codigo al correo y pasa al paso de verificacion", async () => {
    forgotPasswordRequest.mockResolvedValue({ codigo_enviado: true, destinatario: "ana@test.com" });

    render(<ForgotPasswordPage />);

    await act(async () => {
      await userEvent.type(screen.getByLabelText(/correo electronico/i), "ana@test.com");
      await userEvent.click(screen.getByRole("button", { name: /enviar codigo/i }));
    });

    expect(forgotPasswordRequest).toHaveBeenCalledWith("ana@test.com");
    expect(await screen.findByText(/enviamos un codigo de verificacion/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/codigo de verificacion/i)).toBeInTheDocument();
  });

  it("valida el codigo y cambia la contrasena", async () => {
    forgotPasswordRequest.mockResolvedValue({ codigo_enviado: true });
    verifyResetCodeRequest.mockResolvedValue({ reset_token: "tok-123" });
    resetPasswordRequest.mockResolvedValue({ mensaje: "Contrasena actualizada exitosamente" });

    render(<ForgotPasswordPage />);

    await act(async () => {
      await userEvent.type(screen.getByLabelText(/correo electronico/i), "ana@test.com");
      await userEvent.click(screen.getByRole("button", { name: /enviar codigo/i }));
    });

    await act(async () => {
      await userEvent.type(screen.getByLabelText(/codigo de verificacion/i), "123456");
      await userEvent.click(screen.getByRole("button", { name: /verificar codigo/i }));
    });

    expect(verifyResetCodeRequest).toHaveBeenCalledWith("ana@test.com", "123456");
    expect(screen.getByLabelText(/nueva contrasena/i)).toBeInTheDocument();

    await act(async () => {
      await userEvent.type(screen.getByLabelText(/nueva contrasena/i), "NuevaClave1!");
      await userEvent.type(screen.getByLabelText(/confirmar contrasena/i), "NuevaClave1!");
      await userEvent.click(screen.getByRole("button", { name: /cambiar contrasena/i }));
    });

    expect(resetPasswordRequest).toHaveBeenCalledWith({
      email: "ana@test.com",
      codigo: "123456",
      token: "tok-123",
      newPassword: "NuevaClave1!",
    });
    expect(await screen.findByText(/contrasena actualizada/i)).toBeInTheDocument();
  });

  it("muestra el error cuando el codigo es incorrecto", async () => {
    forgotPasswordRequest.mockResolvedValue({ codigo_enviado: true });
    verifyResetCodeRequest.mockRejectedValue({ response: { data: { error: "Codigo incorrecto. Intentos restantes: 2" } } });

    render(<ForgotPasswordPage />);

    await act(async () => {
      await userEvent.type(screen.getByLabelText(/correo electronico/i), "ana@test.com");
      await userEvent.click(screen.getByRole("button", { name: /enviar codigo/i }));
    });

    await act(async () => {
      await userEvent.type(screen.getByLabelText(/codigo de verificacion/i), "000000");
      await userEvent.click(screen.getByRole("button", { name: /verificar codigo/i }));
    });

    expect(await screen.findByText(/codigo incorrecto/i)).toBeInTheDocument();
    expect(resetPasswordRequest).not.toHaveBeenCalled();
  });

  it("valida la politica de contrasena antes de enviar", async () => {
    forgotPasswordRequest.mockResolvedValue({ codigo_enviado: true });
    verifyResetCodeRequest.mockResolvedValue({ reset_token: "tok-123" });

    render(<ForgotPasswordPage />);

    await act(async () => {
      await userEvent.type(screen.getByLabelText(/correo electronico/i), "ana@test.com");
      await userEvent.click(screen.getByRole("button", { name: /enviar codigo/i }));
    });

    await act(async () => {
      await userEvent.type(screen.getByLabelText(/codigo de verificacion/i), "123456");
      await userEvent.click(screen.getByRole("button", { name: /verificar codigo/i }));
    });

    await act(async () => {
      await userEvent.type(screen.getByLabelText(/nueva contrasena/i), "debil");
      await userEvent.type(screen.getByLabelText(/confirmar contrasena/i), "debil");
      await userEvent.click(screen.getByRole("button", { name: /cambiar contrasena/i }));
    });

    expect(await screen.findByText(/al menos 8 caracteres/i)).toBeInTheDocument();
    expect(resetPasswordRequest).not.toHaveBeenCalled();
  });
});