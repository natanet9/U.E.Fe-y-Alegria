import axios from "axios";

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "/api",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

apiClient.interceptors.request.use((config) => {
  try {
    config.headers["X-Timezone"] = Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch (e) {
    config.headers["X-Timezone"] = "America/La_Paz";
  }
  return config;
});

export default apiClient;