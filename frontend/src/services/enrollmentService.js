import apiClient from "./apiClient";

export async function searchExistingStudent(ci) {
  const response = await apiClient.get("/enrollment/search/", {
    params: { rude: ci, ci },
  });
  return response.data;
}

export async function searchTutorByCI(ci) {
  const response = await apiClient.get("/enrollment/search-tutor/", {
    params: { ci },
  });
  return response.data;
}

export async function enrollNewStudent(payload) {
  const tutor = payload.tutor_data
    ? {
        ci: payload.tutor_data.ci,
        nombres: payload.tutor_data.nombre || payload.tutor_data.nombres || "",
        primer_apellido: payload.tutor_data.primer_apellido || payload.tutor_data.primer_apellido || "",
        celular: payload.tutor_data.telefono || payload.tutor_data.celular || "",
        parentesco: payload.tutor_data.parentesco || "",
      }
    : undefined;
  const body = {
    estudiante: {
      rude: payload.rude,
      ci: payload.ci,
      nombres: payload.nombres,
      primer_apellido: payload.primer_apellido,
      segundo_apellido: payload.segundo_apellido || "",
      fecha_nacimiento: payload.fecha_nacimiento || undefined,
      genero: payload.genero || undefined,
    },
    tutor,
    curso_id: payload.curso_id || payload.grado_id,
    gestion: payload.gestion || undefined,
  };
  const response = await apiClient.post("/enrollment/new/", body);
  return response.data;
}

export async function reEnrollStudent(termino, cursoId) {
  const response = await apiClient.post("/enrollment/re-enroll/", {
    rude: termino,
    ci: termino,
    curso_id: cursoId,
  });
  return response.data;
}

export async function getEnrollmentCatalogs() {
  const response = await apiClient.get("/enrollment/catalogs/");
  return response.data;
}

export async function promocionarEstudiantes(origenCursoId, destinoCursoId, origenGestion, destinoGestion) {
  const response = await apiClient.post("/enrollment/promote/", {
    origen_curso_id: origenCursoId,
    destino_curso_id: destinoCursoId,
    origen_gestion: origenGestion,
    destino_gestion: destinoGestion,
  });
  return response.data;
}

export async function promocionarEstudianteIndividual(estudianteId, destinoCursoId, destinoGestion) {
  const response = await apiClient.post("/enrollment/promote/individual/", {
    estudiante_id: estudianteId,
    destino_curso_id: destinoCursoId,
    destino_gestion: destinoGestion,
  });
  return response.data;
}
