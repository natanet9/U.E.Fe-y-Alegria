import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../../src/services/apiClient", () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

import apiClient from "../../../src/services/apiClient";
import {
  changePasswordRequest,
  getCurrentUser,
  getStoredUser,
  isAuthenticated,
  loginRequest,
  logout,
  logoutRequest,
} from "../../../src/services/authService";

describe("authService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("loginRequest guarda usuario en localStorage (token va en cookie httpOnly)", async () => {
    const usuario = { id: "u-1", nombre: "Ana" };
    apiClient.post.mockResolvedValue({
      data: {
        token: "token-123",
        usuario,
      },
    });

    const result = await loginRequest("ana@test.com", "secret");

    expect(apiClient.post).toHaveBeenCalledWith("/auth/login/", {
      email: "ana@test.com",
      password: "secret",
    });
    expect(result).toEqual(usuario);
    expect(JSON.parse(localStorage.getItem("auth_user"))).toEqual(usuario);
  });

  it("getCurrentUser devuelve usuario desde /auth/me", async () => {
    const usuario = { id: "u-2", nombre: "Luis" };
    apiClient.get.mockResolvedValue({ data: { usuario } });

    const result = await getCurrentUser();

    expect(apiClient.get).toHaveBeenCalledWith("/auth/me/");
    expect(result).toEqual(usuario);
  });

  it("getStoredUser retorna null con JSON invalido", () => {
    localStorage.setItem("auth_user", "not-json");
    expect(getStoredUser()).toBeNull();
  });

  it("logout limpia auth_user", () => {
    localStorage.setItem("auth_user", JSON.stringify({ id: "u-3" }));

    logout();

    expect(localStorage.getItem("auth_user")).toBeNull();
  });

  it("logoutRequest limpia estado local aunque falle el backend", async () => {
    localStorage.setItem("auth_user", JSON.stringify({ id: "u-4" }));
    apiClient.post.mockRejectedValue(new Error("backend down"));

    await logoutRequest();

    expect(apiClient.post).toHaveBeenCalledWith("/auth/logout/");
    expect(localStorage.getItem("auth_user")).toBeNull();
  });

  it("changePasswordRequest delega al endpoint correcto", async () => {
    apiClient.post.mockResolvedValue({ data: { ok: true } });

    const result = await changePasswordRequest("old-pass", "new-pass");

    expect(apiClient.post).toHaveBeenCalledWith("/auth/change-password/", {
      current_password: "old-pass",
      new_password: "new-pass",
    });
    expect(result).toEqual({ ok: true });
  });

  it("isAuthenticated es true en modo desarrollo", () => {
    expect(isAuthenticated()).toBe(true);
  });
});