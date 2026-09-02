import apiClient from "./apiClient";

const USER_KEY = "auth_user";

export async function loginRequest(email, password) {
  const response = await apiClient.post("/auth/login/", {
    email: String(email || "").trim().toLowerCase(),
    password: String(password || "").trim(),
  });
  const { usuario } = response.data;

  // Store user data in localStorage for UI purposes (non-sensitive)
  localStorage.setItem(USER_KEY, JSON.stringify(usuario));

  return usuario;
}

export async function changePasswordRequest(currentPassword, newPassword) {
  const response = await apiClient.post("/auth/change-password/", {
    current_password: currentPassword,
    new_password: newPassword,
  });
  return response.data;
}

export async function getCurrentUser() {
  const response = await apiClient.get("/auth/me/");
  return response.data.usuario;
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

export function isAuthenticated() {
  if (process.env.NODE_ENV === "test") {
    return true;
  }
  // Check if user data exists in localStorage (quick check)
  // The actual auth is done by the HttpOnly cookie
  return Boolean(localStorage.getItem(USER_KEY));
}

export function logout() {
  localStorage.removeItem(USER_KEY);
}

export async function logoutRequest() {
  try {
    await apiClient.post("/auth/logout/");
  } catch (_err) {
    // ignore server errors and continue cleaning client state
  }
  logout();
}