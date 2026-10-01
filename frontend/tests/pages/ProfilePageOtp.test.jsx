import { beforeEach, describe, expect, it, vi } from "vitest";
import { act } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("../../src/services/apiClient", () => ({
  default: { put: vi.fn(), get: vi.fn() },
}));

vi.mock("../../src/services/authService", () => ({
  getStoredUser: vi.fn(() => ({ id: 1, nombre: "Ana", rol: "tutor" })),
  changePasswordRequest: vi.fn(),
  otpStatusRequest: vi.fn(),
  otpSetupRequest: vi.fn(),
  otpEnableRequest: vi.fn(),
  otpDisableRequest: vi.fn(),
}));

import {
  otpDisableRequest,
  otpEnableRequest,
  otpSetupRequest,
  otpStatusRequest,
} from "../../src/services/authService";
import ProfilePage from "../../src/pages/auth/ProfilePage";

describe("ProfilePage - verificacion en dos pasos", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("muestra el estado desactivado y activa la 2FA con Google Authenticator", async () => {
    otpStatusRequest.mockResolvedValue({
      otp_habilitado: false,
      otp_metodo: "totp",
      email_enmascarado: "an***@test.com",
      opciones: ["totp"],
    });
    otpSetupRequest.mockResolvedValue({
      metodo: "totp",
      secreto: "JBSWY3DPEHPK3PXP",
      qr_code: "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjwvc3ZnPg==",
      otpauth_uri: "otpauth://totp/UE:ana?secret=JBSWY3DPEHPK3PXP",
      mensaje: "Escanea el código QR con Google Authenticator",
    });
    otpEnableRequest.mockResolvedValue({ otp_habilitado: true, otp_metodo: "totp" });

    render(<ProfilePage />);

    expect(await screen.findByText(/desactivado/i)).toBeInTheDocument();

    await act(async () => {
      await userEvent.click(screen.getByRole("button", { name: /google authenticator/i }));
    });

    expect(otpSetupRequest).toHaveBeenCalledWith("totp");
    expect(await screen.findByAltText(/código qr de autenticación/i)).toBeInTheDocument();
    expect(screen.getByText("JBSWY3DPEHPK3PXP")).toBeInTheDocument();
    expect(await screen.findByLabelText(/de 6 dígitos/i)).toBeInTheDocument();

    await act(async () => {
      await userEvent.type(screen.getByLabelText(/de 6 dígitos/i), "123456");
      await userEvent.click(screen.getByRole("button", { name: /confirmar activación/i }));
    });

    expect(otpEnableRequest).toHaveBeenCalledWith("123456");
    expect(await screen.findByText(/verificación en dos pasos activada/i)).toBeInTheDocument();
  });


  it("permite desactivar la 2FA con la contrasena actual", async () => {
    otpStatusRequest.mockResolvedValue({
      otp_habilitado: true,
      otp_metodo: "totp",
      email_enmascarado: "an***@test.com",
    });
    otpDisableRequest.mockResolvedValue({ otp_habilitado: false });

    render(<ProfilePage />);

    expect(await screen.findByText(/activado \(totp\)/i)).toBeInTheDocument();

    await act(async () => {
      await userEvent.type(screen.getByLabelText(/contraseña actual/i), "NuevaClave1!");
      await userEvent.click(screen.getByRole("button", { name: /^desactivar$/i }));
    });

    expect(otpDisableRequest).toHaveBeenCalledWith({ password: "NuevaClave1!" });
    expect(await screen.findByText(/verificación en dos pasos desactivada/i)).toBeInTheDocument();
  });

  it("muestra el código QR y activa la 2FA con Google Authenticator", async () => {
    otpStatusRequest.mockResolvedValue({
      otp_habilitado: false,
      otp_metodo: "totp",
      email_enmascarado: "an***@test.com",
      opciones: ["email", "totp"],
    });
    otpSetupRequest.mockResolvedValue({
      metodo: "totp",
      secreto: "JBSWY3DPEHPK3PXP",
      qr_code: "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjwvc3ZnPg==",
      otpauth_uri: "otpauth://totp/UE:ana?secret=JBSWY3DPEHPK3PXP",
      mensaje: "Escanea el código QR con Google Authenticator",
    });
    otpEnableRequest.mockResolvedValue({ otp_habilitado: true, otp_metodo: "totp" });

    render(<ProfilePage />);

    await act(async () => {
      await userEvent.click(screen.getByRole("button", { name: /google authenticator/i }));
    });

    expect(otpSetupRequest).toHaveBeenCalledWith("totp");
    expect(await screen.findByAltText(/código qr de autenticación/i)).toBeInTheDocument();
    expect(screen.getByText("JBSWY3DPEHPK3PXP")).toBeInTheDocument();

    await act(async () => {
      await userEvent.type(screen.getByLabelText(/de 6 dígitos/i), "654321");
      await userEvent.click(screen.getByRole("button", { name: /confirmar activación/i }));
    });

    expect(otpEnableRequest).toHaveBeenCalledWith("654321");
    expect(await screen.findByText(/verificación en dos pasos activada/i)).toBeInTheDocument();
  });
});