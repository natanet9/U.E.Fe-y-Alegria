import apiClient from "./apiClient";

const USER_KEY = "auth_user";
const OTP_KEY = "auth_otp_challenge";

export function storeUser(usuario) {
  if (usuario) {
    localStorage.setItem(USER_KEY, JSON.stringify(usuario));
  }
  return usuario;
}

export function clearUser() {
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(OTP_KEY);
  localStorage.removeItem("reset_token");
}

export function storeOtpChallenge(challenge) {
  if (challenge) {
    localStorage.setItem(OTP_KEY, JSON.stringify(challenge));
  }
  return challenge;
}

export function getOtpChallenge() {
  const raw = localStorage.getItem(OTP_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch (_err) {
    return null;
  }
}

export function clearOtpChallenge() {
  localStorage.removeItem(OTP_KEY);
}

/**
 * Paso 1 del login. Devuelve un objeto con la forma:
 *   { requires_otp: true, otp_token, metodo, destinatario, usuario }
 * o el usuario autenticado cuando la cuenta no usa segundo factor.
 */
export async function loginRequest(email, password) {
  const response = await apiClient.post("/auth/login/", {
    email: String(email || "").trim().toLowerCase(),
    password: String(password || "").trim(),
  });

  const data = response.data || {};

  if (data.requires_otp) {
    storeOtpChallenge({
      otp_token: data.otp_token,
      metodo: data.metodo,
      destinatario: data.destinatario || null,
      expira_en_minutos: data.expira_en_minutos,
      correo_enviado: data.correo_enviado,
      mensaje: data.mensaje,
      email: String(email || "").trim().toLowerCase(),
    });
    return data;
  }

  clearOtpChallenge();
  return storeUser(data.usuario);
}

/** Paso 2 del login: valida el codigo OTP y guarda la sesion. */
export async function verifyOtpRequest(otpToken, codigo) {
  const response = await apiClient.post("/auth/verify-otp/", {
    otp_token: otpToken,
    codigo: String(codigo || "").trim(),
  });
  const { usuario } = response.data;
  clearOtpChallenge();
  storeUser(usuario);
  return usuario;
}

export async function resendOtpRequest(otpToken) {
  const response = await apiClient.post("/auth/2fa/reenviar/", { otp_token: otpToken });
  return response.data;
}

export async function changePasswordRequest(currentPassword, newPassword) {
  const response = await apiClient.post("/auth/change-password/", {
    current_password: currentPassword,
    new_password: newPassword,
  });

  const usuario = response.data?.usuario;
  if (usuario) {
    storeUser(usuario);
  } else {
    const stored = getStoredUser();
    if (stored) {
      stored.debe_cambiar_password = false;
      stored.password_temporal = false;
      storeUser(stored);
    }
  }
  return response.data;
}

export async function forgotPasswordRequest(email) {
  const response = await apiClient.post("/auth/forgot-password/", {
    email: String(email || "").trim().toLowerCase(),
  });
  return response.data;
}

export async function verifyResetCodeRequest(email, codigo) {
  const response = await apiClient.post("/auth/verify-reset-code/", {
    email: String(email || "").trim().toLowerCase(),
    codigo: String(codigo || "").trim(),
  });
  if (response.data?.reset_token) {
    localStorage.setItem("reset_token", response.data.reset_token);
  }
  return response.data;
}

export async function resetPasswordRequest({ email, codigo, token, newPassword }) {
  const resetToken = token || (typeof window !== "undefined" ? localStorage.getItem("reset_token") : null);
  const payload = { new_password: newPassword };
  if (resetToken) {
    payload.token = resetToken;
  }
  if (email && codigo) {
    payload.email = String(email).trim().toLowerCase();
    payload.codigo = String(codigo).trim();
  }
  const response = await apiClient.post("/auth/reset-password/", payload);
  if (typeof window !== "undefined") {
    localStorage.removeItem("reset_token");
  }
  return response.data;
}

// ─ Autenticacion en dos pasos (2FA) ────────────────────────────────────────
export async function otpStatusRequest() {
  const response = await apiClient.get("/auth/2fa/");
  return response.data;
}

export async function otpSetupRequest(metodo = "email") {
  const response = await apiClient.post("/auth/2fa/setup/", { metodo });
  return response.data;
}

export async function otpEnableRequest(codigo) {
  const response = await apiClient.post("/auth/2fa/enable/", { codigo: String(codigo || "").trim() });
  return response.data;
}

export async function otpDisableRequest({ password, codigo } = {}) {
  const payload = {};
  if (password) payload.password = password;
  if (codigo) payload.codigo = String(codigo).trim();
  const response = await apiClient.post("/auth/2fa/disable/", payload);
  return response.data;
}

export async function getCurrentUser() {
  const response = await apiClient.get("/auth/me/");
  return storeUser(response.data.usuario);
}

export function getStoredUser() {
  const rawUser = localStorage.getItem(USER_KEY);
  if (!rawUser) {
    return null;
  }

  try {
    return JSON.parse(rawUser);
  } catch (_err) {
    return null;
  }
}

export function needsPasswordChange() {
  return Boolean(getStoredUser()?.debe_cambiar_password);
}

export function isAuthenticated() {
  if (process.env.NODE_ENV === "test") {
    return true;
  }
  // Check if user data exists in localStorage (quick check)
  // The actual auth is done by the HttpOnly cookie
  return Boolean(localStorage.getItem(USER_KEY));
}

export function logout() {
  clearUser();
}

export async function logoutRequest() {
  try {
    await apiClient.post("/auth/logout/");
  } catch (_err) {
    // ignore server errors and continue cleaning client state
  }
  logout();
}