import apiClient from "./apiClient";

export async function getSchedulesPage({ gradoId = "" } = {}) {
  const params = new URLSearchParams();
  if (gradoId) {
    params.append("grado_id", gradoId);
  }

  const queryString = params.toString();
  const url = queryString ? `/schedules/?${queryString}` : "/schedules/";

  return apiClient
    .get(url)
    .then((response) => response.data)
    .catch((error) => {
      if (error.response?.status === 401) {
        throw new Error("No autorizado");
      }
      throw error;
    });
}

export async function createSchedule(payload) {
  const response = await apiClient.post("/schedules/", payload);
  return response.data;
}

export async function updateSchedule(scheduleId, payload) {
  const response = await apiClient.put(`/schedules/${scheduleId}/`, payload);
  return response.data;
}

export async function deleteSchedule(scheduleId) {
  const response = await apiClient.delete(`/schedules/${scheduleId}/`);
  return response.data;
}
