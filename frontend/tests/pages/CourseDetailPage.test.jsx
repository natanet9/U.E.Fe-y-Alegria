import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("../../src/services/coursesService", () => ({
  getCourseDetail: vi.fn(),
  updateGrades: vi.fn(),
}));

vi.mock("../../src/services/attendanceService", () => ({
  markAttendance: vi.fn(),
  getAttendance: vi.fn(),
}));

vi.mock("../../src/services/activitiesService", () => ({
  default: {
    createActividad: vi.fn(),
    deleteActividad: vi.fn(),
    updateActividadesNotas: vi.fn(),
    updateActividadesNotasBatch: vi.fn(),
    recomputeTrimestre: vi.fn(),
  },
}));

vi.mock("../../src/services/authService", () => ({
  getStoredUser: vi.fn(),
}));

import { getCourseDetail } from "../../src/services/coursesService";
import { markAttendance, getAttendance } from "../../src/services/attendanceService";
import { getStoredUser } from "../../src/services/authService";
import CourseDetailPage from "../../src/pages/cursos/CourseDetailPage";

const mockCursoData = {
  curso: { grado: "6°", paralelo: "A", nivel: "Primaria", area: "Matemáticas" },
  estudiantes: [
    { id: 1, nombres: "Juan", primer_apellido: "Pérez" },
    { id: 2, nombres: "María", primer_apellido: "García" },
  ],
  periodos: [{ id: 1, nombre: "T1", activo: true }],
  dimensiones: [{ id: 1, nombre: "Dimensión 1", puntaje_maximo: 50 }],
  actividades: [],
  actividad_notas: {},
  notas_dimension: {},
  cerrado: false,
  asignaciones: [],
};

const mockAttendanceData = [
  { estudiante_id: 1, estado: "presente" },
  { estudiante_id: 2, estado: "ausente" },
];

function renderComponent(path) {
  return render(
    <MemoryRouter initialEntries={[path || "/cursos/detalle?docente_asignacion_id=123"]}>
      <CourseDetailPage />
    </MemoryRouter>,
  );
}

describe("CourseDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getStoredUser.mockReturnValue({ rol: "docente", nombre: "Docente Test" });
    getCourseDetail.mockResolvedValue(mockCursoData);
    getAttendance.mockResolvedValue(mockAttendanceData);
  });

  it("muestra el estado de carga inicialmente", () => {
    getCourseDetail.mockImplementation(() => new Promise(() => {}));
    renderComponent();
    expect(screen.getByText("Cargando...")).toBeInTheDocument();
  });

  it("muestra mensaje cuando no hay docente_asignacion_id", () => {
    renderComponent("/cursos/detalle");
    expect(screen.getByText("Asignación no especificada")).toBeInTheDocument();
  });

  it("renderiza los datos del curso detalle", async () => {
    renderComponent();
    expect(await screen.findByText("6° A · Primaria")).toBeInTheDocument();
    expect(screen.getByText("Matemáticas")).toBeInTheDocument();
    expect(screen.getByText(/juan/i)).toBeInTheDocument();
    expect(screen.getByText(/maría/i)).toBeInTheDocument();
  });

  it("muestra el estado abierto cuando cerrado es false", async () => {
    renderComponent();
    expect(await screen.findByText("✓ Abierto")).toBeInTheDocument();
  });

  it("muestra el estado cerrado cuando cerrado es true", async () => {
    getCourseDetail.mockResolvedValue({ ...mockCursoData, cerrado: true });
    renderComponent();
    expect(await screen.findByText("🔒 Cerrado")).toBeInTheDocument();
  });

  it("deshabilita el input de fecha para docentes", async () => {
    renderComponent();
    const dateInput = await screen.findByDisplayValue(/^\d{4}-\d{2}-\d{2}$/);
    expect(dateInput).toBeDisabled();
  });

  it("alterna el estado de asistencia al hacer clic", async () => {
    renderComponent();
    const presenteBtn = await screen.findByText("Presente");
    fireEvent.click(presenteBtn);
    await waitFor(() => {
      expect(screen.queryByText("Presente")).not.toBeInTheDocument();
    });
  });

  it("cambia entre pestañas de Asistencia y Notas", async () => {
    renderComponent();
    expect(await screen.findByText("Asistencia")).toBeInTheDocument();
    const notasTab = screen.getByRole("button", { name: "Notas" });
    fireEvent.click(notasTab);
    expect(screen.getByText("Nueva actividad")).toBeInTheDocument();
  });

  it("llama a markAttendance al guardar asistencia", async () => {
    markAttendance.mockResolvedValue({});
    renderComponent();
    await screen.findByText("Presente");
    fireEvent.click(screen.getByText("Guardar asistencia"));
    await waitFor(() => {
      expect(markAttendance).toHaveBeenCalled();
    });
  });
});
