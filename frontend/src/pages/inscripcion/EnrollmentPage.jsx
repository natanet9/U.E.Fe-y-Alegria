import { useEffect, useState, useCallback } from "react";
import { searchExistingStudent, searchTutorByCI, enrollNewStudent, reEnrollStudent, getEnrollmentCatalogs, promocionarEstudianteIndividual } from "../../services/enrollmentService";
import Toast from "../../components/Toast";

const EMPTY_ARRAY = [];

function SearchStudentCard({ estudiante, onSelect }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm hover:shadow-md transition">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-800 flex items-center justify-center font-semibold">
              {estudiante.nombre.split(' ').map(n=>n[0]).slice(0,2).join('')}
            </div>
            <div>
              <p className="font-semibold text-slate-900">{estudiante.nombre}</p>
              <p className="text-xs text-slate-500">R.U.D.E.: {estudiante.rude || estudiante.ci}</p>
            </div>
          </div>
          <p className="text-sm text-slate-600 mt-2">
            Grado actual: <span className="font-semibold">{estudiante.grado_actual_nombre || "No asignado"}</span>
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Estado: {estudiante.estado === "activo" ? <span className="text-green-600 font-semibold">Activo</span> : <span className="text-yellow-600 font-semibold">Inactivo (disponible para reinscripción)</span>}
          </p>
        </div>
        <button
          type="button"
          onClick={() => onSelect(estudiante)}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-bold text-white hover:bg-blue-700"
        >
          Seleccionar
        </button>
      </div>
    </div>
  );
}

function EnrollmentPage() {
  const [tab, setTab] = useState("search"); // "search" or "new"
  const [catalogs, setCatalogs] = useState({ grados: EMPTY_ARRAY, cursos: EMPTY_ARRAY, tutores: EMPTY_ARRAY });

  // Promote State (integrated in search tab)
  const [promoteDestinoCurso, setPromoteDestinoCurso] = useState("");
  const [promoteDestinoGestion, setPromoteDestinoGestion] = useState(new Date().getFullYear() + 1);
  const [promoting, setPromoting] = useState(false);

  // Search Tab State
  const [searchCI, setSearchCI] = useState("");
  const [searchLoading, setSearchLoading] = useState(false);
  const [foundStudent, setFoundStudent] = useState(null);
  const [selectedCursoForReEnroll, setSelectedCursoForReEnroll] = useState("");
  const [reEnrolling, setReEnrolling] = useState(false);

  // Auto-set destino curso when student is reprobado
  useEffect(() => {
    if (foundStudent?.estado === "activo" && foundStudent.aprobado === false && foundStudent.curso_actual_id) {
      setPromoteDestinoCurso(String(foundStudent.curso_actual_id));
    }
  }, [foundStudent]);

  // New Enrollment Tab State
  const [newForm, setNewForm] = useState({
    nombres: "",
    primer_apellido: "",
    segundo_apellido: "",
    rude: "",
    ci: "",
    fecha_nacimiento: "",
    genero: "",
    curso_id: "",
    tutor_data: null,
  });
  const [newLoading, setNewLoading] = useState(false);
  const [toast, setToast] = useState({ mensaje: "", tipo: "success" });

  const showToast = useCallback((tipo, mensaje) => {
    setToast({ mensaje, tipo });
  }, []);

  const closeToast = useCallback(() => {
    setToast({ mensaje: "", tipo: "success" });
  }, []);

  // Tutor Search State
  const [tutorSearchCI, setTutorSearchCI] = useState("");
  const [tutorSearching, setTutorSearching] = useState(false);
  const [foundTutor, setFoundTutor] = useState(null);
  const [tutorFormData, setTutorFormData] = useState({
    nombre: "",
    primer_apellido: "",
    ci: "",
    telefono: "",
    ocupacion: "",
    direccion: "",
  });
  const [showTutorForm, setShowTutorForm] = useState(false);

  useEffect(() => {
    let mounted = true;

    getEnrollmentCatalogs()
      .then((response) => {
        if (!mounted) return;
        setCatalogs(response);
      })
      .catch((err) => {
        if (!mounted) return;
        showToast("error", err?.response?.data?.error || "No fue posible cargar los catálogos");
      });

    return () => {
      mounted = false;
    };
  }, []);

  const handleSearchChange = (e) => {
    setSearchCI(e.target.value);
    setFoundStudent(null);
  };

  const handleSearchStudent = async () => {
    if (!searchCI.trim()) {
      showToast("error", "Debes ingresar un C.I. o R.U.D.E.");
      return;
    }

    setSearchLoading(true);
    setFoundStudent(null);

    try {
      const resultado = await searchExistingStudent(searchCI.trim());
      if (resultado.encontrado) {
        setFoundStudent(resultado.estudiante);
        setSelectedCursoForReEnroll("");
      } else {
        showToast("error", "No se encontró estudiante con ese C.I. Usa la sección de Inscripción Nueva.");
      }
    } catch (err) {
      showToast("error", err?.response?.data?.error || "Error al buscar estudiante");
    } finally {
      setSearchLoading(false);
    }
  };

  const handleReEnroll = async () => {
    if (!foundStudent || !selectedCursoForReEnroll) {
      showToast("error", "Debes seleccionar un curso");
      return;
    }

    setReEnrolling(true);

    try {
      const resultado = await reEnrollStudent(foundStudent.rude || foundStudent.ci, selectedCursoForReEnroll);
      setFoundStudent(null);
      setSearchCI("");
      setSelectedCursoForReEnroll("");
      showToast("success", resultado.mensaje);
    } catch (err) {
      showToast("error", err?.response?.data?.error || "Error al reinscribir");
    } finally {
      setReEnrolling(false);
    }
  };

  const handleNewFormChange = (e) => {
    const { name, value } = e.target;
    setNewForm((current) => ({ ...current, [name]: value }));
  };

  const handleTutorFormChange = (e) => {
    const { name, value } = e.target;
    setTutorFormData((current) => ({ ...current, [name]: value }));
  };

  const handleSearchTutor = async () => {
    const ci = tutorSearchCI.trim();
    if (!ci) {
      return;
    }

    setTutorSearching(true);
    try {
      const resultado = await searchTutorByCI(ci);
      if (resultado.encontrado) {
        setFoundTutor(resultado.tutor);
        setNewForm((current) => ({ ...current, tutor_data: resultado.tutor }));
        setShowTutorForm(false);
      } else {
        setFoundTutor(null);
        setTutorFormData({ nombre: "", primer_apellido: "", ci, telefono: "", ocupacion: "", direccion: "" });
        setShowTutorForm(true);
      }
    } catch (err) {
      console.error("Error buscando tutor:", err);
    } finally {
      setTutorSearching(false);
    }
  };

  const handleAddNewTutor = () => {
    const { nombre, ci } = tutorFormData;
    if (!nombre.trim() || !ci.trim()) {
      showToast("error", "Debes ingresar el nombre y CI del tutor");
      return;
    }
    setFoundTutor(tutorFormData);
    setNewForm((current) => ({ ...current, tutor_data: tutorFormData }));
    setShowTutorForm(false);
    setTutorSearchCI("");
  };

  const handleClearTutor = () => {
    setFoundTutor(null);
    setTutorSearchCI("");
    setShowTutorForm(false);
    setTutorFormData({ nombre: "", primer_apellido: "", ci: "", telefono: "", ocupacion: "", direccion: "" });
    setNewForm((current) => ({ ...current, tutor_data: null }));
  };

  const handleEnrollNew = async (e) => {
    e.preventDefault();
    if (!newForm.nombres || !newForm.primer_apellido || !newForm.rude || !newForm.ci || !newForm.curso_id) {
      showToast("error", "Debes llenar: nombres, primer apellido, RUDE, documento de identidad y curso");
      return;
    }

    setNewLoading(true);

    try {
      const resultado = await enrollNewStudent(newForm);
      showToast("success", resultado.mensaje);
      setNewForm({
        nombres: "",
        primer_apellido: "",
        segundo_apellido: "",
        rude: "",
        ci: "",
        fecha_nacimiento: "",
        genero: "",
        curso_id: "",
        tutor_data: null,
      });
      handleClearTutor();
    } catch (err) {
      showToast("error", err?.response?.data?.error || "Error al inscribir estudiante");
    } finally {
      setNewLoading(false);
    }
  };

  return (

    <section className="space-y-6">
      <Toast mensaje={toast.mensaje} tipo={toast.tipo} onClose={closeToast} />
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(99,102,241,0.08),rgba(255,255,255,0.94),rgba(14,165,233,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
          <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Inscripción de Estudiantes</h1>
          <p className="mt-2 max-w-2xl text-base text-slate-600">
            Gestiona la inscripción y reinscripción de estudiantes. El sistema detecta automáticamente si el estudiante ya fue inscrito anteriormente.
          </p>
        </div>
      </header>

      <div className="grid gap-4 lg:grid-cols-[1.3fr_0.9fr]">
        <div className="rounded-[2rem] border border-blue-200 bg-blue-50 p-6 text-sm text-blue-900 shadow-[0_12px_40px_rgba(37,99,235,0.08)]">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-blue-600">Puntos clave</p>
          <h2 className="mt-2 text-lg font-bold text-slate-950">Inscripción y reinscripción</h2>
          <ul className="mt-4 space-y-2 text-sm leading-6 text-slate-700">
            <li>• Para buscar o reinscribir a un estudiante ingresa su C.I.</li>
            <li>• Si el estudiante ya existe, el sistema lo detecta y permite reinscribirlo solo si está inactivo.</li>
            <li>• En la inscripción nueva debes completar nombres, primer apellido, RUDE y grado.</li>
            <li>• También puedes buscar un tutor existente o registrar uno nuevo antes de guardar.</li>
          </ul>
        </div>
        <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_12px_40px_rgba(15,23,42,0.05)]">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Nota</p>
          <p className="mt-2 text-sm text-slate-600">
            Si me compartes el PDF, ajusto esta sección con los puntos exactos del documento.
          </p>
        </div>
      </div>

      <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <div className="flex gap-4 border-b border-slate-100">
          <button
            type="button"
            onClick={() => {
              setTab("search");
            }}
            className={`px-4 py-3 font-semibold transition ${
              tab === "search"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            🔍 Reinscripción
          </button>
          <button
            type="button"
            onClick={() => {
              setTab("new");
            }}
            className={`px-4 py-3 font-semibold transition ${
              tab === "new"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            ➕ Inscripción Nueva
          </button>
        </div>

        {/* Search/Re-enroll Tab */}
        {tab === "search" && (
          <div className="mt-6 space-y-6">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Buscar Estudiante por C.I., R.U.D.E. o Nombre
              </label>
              <p className="text-xs text-slate-500 mb-3">
                Ingresa el C.I., R.U.D.E. o nombre del estudiante. Si está activo, podrás ver su curso actual y promoverlo al siguiente nivel.
              </p>
              <p className="text-xs text-slate-500 mb-3">
                Si el estudiante ya fue inscrito anteriormente (y está inactivo), puedes reinscribirlo aquí.
              </p>
              <div className="flex gap-3">
                <input
                  type="text"
                  placeholder="Ingresa el C.I. del estudiante"
                  value={searchCI}
                  onChange={handleSearchChange}
                  className="flex-1 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                />
                <button
                  type="button"
                  onClick={handleSearchStudent}
                  disabled={searchLoading}
                  className="rounded-2xl bg-blue-600 px-6 py-3 text-sm font-bold text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {searchLoading ? "Buscando..." : "Buscar"}
                </button>
              </div>
            </div>

            {foundStudent && (
              <div className="space-y-4 p-4 rounded-2xl border border-blue-200 bg-blue-50">
                <SearchStudentCard
                  estudiante={foundStudent}
                  onSelect={() => {}}
                />

                {foundStudent.estado !== "activo" && (
                  <div className="space-y-3">
                    <label className="block text-sm font-semibold text-slate-700">
                      Selecciona el nuevo curso para reinscripción:
                    </label>
                    <select
                      value={selectedCursoForReEnroll}
                      onChange={(e) => setSelectedCursoForReEnroll(e.target.value)}
                      className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none"
                    >
                      <option value="">Selecciona un curso...</option>
                      {(catalogs.cursos || catalogs.grados).map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.nombre}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={handleReEnroll}
                      disabled={reEnrolling || !selectedCursoForReEnroll}
                      className="w-full rounded-2xl bg-green-600 px-4 py-3 text-sm font-bold text-white hover:bg-green-700 disabled:opacity-50"
                    >
                      {reEnrolling ? "Reinscribiendo..." : "✅ Reinscribir"}
                    </button>
                  </div>
                )}

                {foundStudent.estado === "activo" && (
                  <div className="space-y-4">
                    <div className="rounded-2xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800">
                      <p className="font-semibold">
                        📘 Curso actual: <span className="text-blue-900">{foundStudent.curso_actual || "Sin asignar"}</span>
                        <span className="ml-3 text-slate-500">(Gestión {foundStudent.gestion_actual})</span>
                      </p>
                      {foundStudent.aprobado === true && (
                        <p className="mt-1 font-semibold text-green-700">
                          ✅ APROBADO — Promedio general: {foundStudent.promedio_general}
                        </p>
                      )}
                      {foundStudent.aprobado === false && (
                        <p className="mt-1 font-semibold text-red-600">
                          ❌ REPROBADO — Promedio general: {foundStudent.promedio_general}
                        </p>
                      )}
                      {foundStudent.aprobado === null && (
                        <p className="mt-1 text-slate-500">
                          ⏳ Sin calificaciones registradas para esta gestión
                        </p>
                      )}
                    </div>

                    <div className="border-t border-blue-100 pt-4">
                      {foundStudent.aprobado === false ? (
                        <div>
                          <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 mb-3">
                            ⚠️ El estudiante ha <strong>REPROBADO</strong> el curso actual. Debe <strong>repetir el curso</strong> en la próxima gestión.
                          </div>
                          <input type="hidden" value={promoteDestinoCurso} />
                          <div className="grid gap-3 sm:grid-cols-2">
                            <div className="rounded-xl border border-slate-200 bg-slate-100 px-4 py-2.5 text-sm text-slate-600">
                              {foundStudent.curso_actual} (repetición)
                            </div>
                            <input
                              type="number"
                              placeholder="Gestión destino"
                              value={promoteDestinoGestion}
                              onChange={(e) => setPromoteDestinoGestion(parseInt(e.target.value) || new Date().getFullYear() + 1)}
                              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm outline-none focus:border-blue-500"
                            />
                          </div>
                          <button
                            type="button"
                            onClick={async () => {
                              if (!window.confirm(
                                `¿Inscribir a ${foundStudent.nombres} ${foundStudent.primer_apellido || ""} para repetir ${foundStudent.curso_actual} (gestión ${promoteDestinoGestion})?\n\n` +
                                `Curso actual: ${foundStudent.curso_actual} (Gestión ${foundStudent.gestion_actual})\n` +
                                `Estado: REPROBADO - Promedio: ${foundStudent.promedio_general || "N/A"}`
                              )) return;
                              setPromoting(true);
                              try {
                                const result = await promocionarEstudianteIndividual(
                                  foundStudent.id,
                                  promoteDestinoCurso,
                                  promoteDestinoGestion
                                );
                                setToast({ mensaje: result.mensaje || "Inscripción para repetición exitosa", tipo: "success" });
                                setFoundStudent(null);
                                setSearchCI("");
                              } catch (err) {
                                setToast({ mensaje: err.response?.data?.error || "Error al inscribir", tipo: "error" });
                              } finally {
                                setPromoting(false);
                              }
                            }}
                            disabled={promoting}
                            className="mt-3 w-full rounded-xl bg-amber-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-amber-700 disabled:opacity-50"
                          >
                            {promoting ? "Inscribiendo..." : "🔄 Repetir curso"}
                          </button>
                        </div>
                      ) : (
                        <div>
                          <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                            Curso destino para promoción:
                          </label>
                          <div className="grid gap-3 sm:grid-cols-2">
                            <select
                              value={promoteDestinoCurso}
                              onChange={(e) => setPromoteDestinoCurso(e.target.value)}
                              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm outline-none focus:border-blue-500"
                            >
                              <option value="">Selecciona un curso...</option>
                              {(catalogs.cursos || catalogs.grados).map((c) => (
                                <option key={c.id} value={c.id}>{c.nombre}</option>
                              ))}
                            </select>
                            <input
                              type="number"
                              placeholder="Gestión destino"
                              value={promoteDestinoGestion}
                              onChange={(e) => setPromoteDestinoGestion(parseInt(e.target.value) || new Date().getFullYear() + 1)}
                              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm outline-none focus:border-blue-500"
                            />
                          </div>
                          <button
                            type="button"
                            onClick={async () => {
                              if (!promoteDestinoCurso) {
                                setToast({ mensaje: "Selecciona un curso de destino", tipo: "error" });
                                return;
                              }
                              if (!window.confirm(
                                `¿Promocionar a ${foundStudent.nombres} ${foundStudent.primer_apellido || ""} al curso seleccionado (gestión ${promoteDestinoGestion})?\n\n` +
                                `Curso actual: ${foundStudent.curso_actual} (Gestión ${foundStudent.gestion_actual})\n` +
                                `Estado: APROBADO - Promedio: ${foundStudent.promedio_general || "N/A"}`
                              )) return;
                              setPromoting(true);
                              try {
                                const result = await promocionarEstudianteIndividual(
                                  foundStudent.id,
                                  promoteDestinoCurso,
                                  promoteDestinoGestion
                                );
                                setToast({ mensaje: result.mensaje || "Promoción exitosa", tipo: "success" });
                                setFoundStudent(null);
                                setSearchCI("");
                              } catch (err) {
                                setToast({ mensaje: err.response?.data?.error || "Error al promocionar", tipo: "error" });
                              } finally {
                                setPromoting(false);
                              }
                            }}
                            disabled={promoting || !promoteDestinoCurso}
                            className="mt-3 w-full rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-bold text-white hover:bg-slate-800 disabled:opacity-50"
                          >
                            {promoting ? "Promocionando..." : "📈 Promover al curso seleccionado"}
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* New Enrollment Tab */}
        {tab === "new" && (
          <form onSubmit={handleEnrollNew} className="mt-6 space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Nombres *
                </label>
                <input
                  type="text"
                  name="nombres"
                  placeholder="Ej: Juan Pablo"
                  value={newForm.nombres}
                  onChange={handleNewFormChange}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Primer Apellido *
                </label>
                <input
                  type="text"
                  name="primer_apellido"
                  placeholder="Ej: García"
                  value={newForm.primer_apellido}
                  onChange={handleNewFormChange}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Segundo Apellido
                </label>
                <input
                  type="text"
                  name="segundo_apellido"
                  placeholder="Ej: López"
                  value={newForm.segundo_apellido}
                  onChange={handleNewFormChange}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  R.U.D.E. *
                </label>
                <input
                  type="text"
                  name="rude"
                  placeholder="Ej: RUDE-2026-0001"
                  value={newForm.rude}
                  onChange={handleNewFormChange}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Documento de identidad *
                </label>
                <input
                  type="text"
                  name="ci"
                  placeholder="Ej: 8-123-456"
                  value={newForm.ci}
                  onChange={handleNewFormChange}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Fecha de Nacimiento
                </label>
                <input
                  type="date"
                  name="fecha_nacimiento"
                  value={newForm.fecha_nacimiento}
                  onChange={handleNewFormChange}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Género
                </label>
                <select
                  name="genero"
                  value={newForm.genero}
                  onChange={handleNewFormChange}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                >
                  <option value="">Selecciona...</option>
                  <option value="M">Masculino</option>
                  <option value="F">Femenino</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Curso *
                </label>
                <select
                  name="curso_id"
                  value={newForm.curso_id}
                  onChange={handleNewFormChange}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                >
                  <option value="">Selecciona un curso...</option>
                  {(catalogs.cursos || catalogs.grados).map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nombre}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Tutor Section */}
            <div className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-900">Asignar Tutor</h3>
                {foundTutor && (
                  <button
                    type="button"
                    onClick={handleClearTutor}
                    className="text-xs text-red-600 hover:text-red-700 font-semibold"
                  >
                    Limpiar
                  </button>
                )}
              </div>

              {!foundTutor ? (
                <div className="space-y-3">
                  <p className="text-xs text-slate-600">
                    Busca un tutor existente por documento de identidad. Si no existe, puedes crearlo y se asignara al estudiante.
                  </p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Ingresa el documento de identidad del tutor"
                      value={tutorSearchCI}
                      onChange={(e) => setTutorSearchCI(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleSearchTutor())}
                      className="flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-blue-300"
                    />
                    <button
                      type="button"
                      onClick={handleSearchTutor}
                      disabled={tutorSearching || !tutorSearchCI.trim()}
                      className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
                    >
                      {tutorSearching ? "..." : "Buscar"}
                    </button>
                  </div>

                  {showTutorForm && (
                    <div className="space-y-3 mt-4 pt-4 border-t border-slate-200">
                      <p className="text-sm font-semibold text-slate-700">Crear nuevo tutor</p>
                      <div className="grid gap-3 md:grid-cols-2">
                        <div>
                          <label className="text-xs font-semibold text-slate-700">Nombre *</label>
                          <input
                            type="text"
                            name="nombre"
                            placeholder="Nombre"
                            value={tutorFormData.nombre}
                            onChange={handleTutorFormChange}
                            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-blue-300"
                          />
                        </div>
                        <div>
                          <label className="text-xs font-semibold text-slate-700">Apellido</label>
                          <input
                            type="text"
                            name="primer_apellido"
                            placeholder="Apellido"
                            value={tutorFormData.primer_apellido}
                            onChange={handleTutorFormChange}
                            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-blue-300"
                          />
                        </div>
                        <div>
                          <label className="text-xs font-semibold text-slate-700">Documento de identidad *</label>
                          <input
                            type="text"
                            name="ci"
                            placeholder="Documento de identidad"
                            value={tutorFormData.ci}
                            onChange={handleTutorFormChange}
                            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-blue-300"
                          />
                        </div>
                        <div>
                          <label className="text-xs font-semibold text-slate-700">Teléfono</label>
                          <input
                            type="text"
                            name="telefono"
                            placeholder="Teléfono"
                            value={tutorFormData.telefono}
                            onChange={handleTutorFormChange}
                            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-blue-300"
                          />
                        </div>
                        <div>
                          <label className="text-xs font-semibold text-slate-700">Ocupación</label>
                          <input
                            type="text"
                            name="ocupacion"
                            placeholder="Ocupación"
                            value={tutorFormData.ocupacion}
                            onChange={handleTutorFormChange}
                            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-blue-300"
                          />
                        </div>
                        <div>
                          <label className="text-xs font-semibold text-slate-700">Dirección</label>
                          <input
                            type="text"
                            name="direccion"
                            placeholder="Dirección"
                            value={tutorFormData.direccion}
                            onChange={handleTutorFormChange}
                            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-blue-300"
                          />
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={handleAddNewTutor}
                        className="w-full rounded-xl bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700"
                      >
                        Agregar Tutor
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="rounded-xl border border-green-200 bg-green-50 p-3">
                  <p className="text-sm font-semibold text-slate-900">
                    {foundTutor.nombre} {foundTutor.primer_apellido}
                  </p>
                  <p className="text-xs text-slate-600">Documento de identidad: {foundTutor.ci}</p>
                  {foundTutor.telefono && <p className="text-xs text-slate-600">Tel: {foundTutor.telefono}</p>}
                </div>
              )}
            </div>

            <div className="flex gap-3 border-t border-slate-100 pt-6">
              <button
                type="submit"
                disabled={newLoading}
                className="rounded-2xl bg-slate-950 px-6 py-3 text-sm font-bold text-white hover:bg-slate-800 disabled:opacity-50"
              >
                {newLoading ? "Inscribiendo..." : "✅ Inscribir Estudiante"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setNewForm({
                    nombres: "",
                    primer_apellido: "",
                    segundo_apellido: "",
                    rude: "",
                    ci: "",
                    fecha_nacimiento: "",
                    genero: "",
                    curso_id: "",
                    tutor_data: null,
                  });
                  handleClearTutor();
                }}
                className="rounded-2xl border border-slate-200 bg-white px-6 py-3 text-sm font-bold text-slate-900 hover:bg-slate-50"
              >
                Limpiar
              </button>
            </div>
          </form>
        )}
      </div>
    </section>
  );
}

export default EnrollmentPage;
