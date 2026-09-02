import { beforeEach, describe, expect, it, vi } from "vitest";
import { act } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("../../../src/services/authService", () => ({
  changePasswordRequest: vi.fn(),
}));

import { changePasswordRequest } from "../../../src/services/authService";
import ChangePasswordForm from "../../../src/components/auth/ChangePasswordForm";

describe("ChangePasswordForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("valida la confirmacion y muestra error", async () => {
    const { container } = render(<ChangePasswordForm />);
    const inputs = container.querySelectorAll('input[type="password"]');

    await act(async () => {
      await userEvent.type(inputs[0], "OldPass1!");
      await userEvent.type(inputs[1], "NewPass1!");
      await userEvent.type(inputs[2], "Mismatch1!");
      await userEvent.click(screen.getByRole("button", { name: /actualizar contraseña/i }));
    });

    expect(await screen.findByText(/no coinciden/i)).toBeInTheDocument();
    expect(changePasswordRequest).not.toHaveBeenCalled();
  });

  it("cambia la contraseña y limpia el formulario", async () => {
    changePasswordRequest.mockResolvedValue({ ok: true });

    const { container } = render(<ChangePasswordForm />);
    const inputs = container.querySelectorAll('input[type="password"]');

    await act(async () => {
      await userEvent.type(inputs[0], "OldPass1!");
      await userEvent.type(inputs[1], "NewPass1!");
      await userEvent.type(inputs[2], "NewPass1!");
      await userEvent.click(screen.getByRole("button", { name: /actualizar contraseña/i }));
    });

    expect(changePasswordRequest).toHaveBeenCalledWith("OldPass1!", "NewPass1!");
    expect(await screen.findByText(/contraseña actualizada/i)).toBeInTheDocument();
  });
});