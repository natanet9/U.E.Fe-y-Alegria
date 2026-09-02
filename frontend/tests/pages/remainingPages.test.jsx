import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

vi.mock("../../src/services/coursesService", () => ({
  getCoursesPage: vi.fn(),
  createCourse: vi.fn(),
  getCourseDetail: vi.fn(),
  updateGrades: vi.fn(),
}));
vi.mock("../../src/services/docentesService", () => ({
  getDocentesPage: vi.fn(),
  createDocente: vi.fn(),
}));
vi.mock("../../src/services/studentsService", () => ({
  getStudentsPage: vi.fn(),
  createStudent: vi.fn(),
}));
vi.mock("../../src/services/schedulesService", () => ({
  getSchedulesPage: vi.fn(),
}));
vi.mock("../../src/services/enrollmentService", () => ({
  searchExistingStudent: vi.fn(),
  enrollNewStudent: vi.fn(),
  reEnrollStudent: vi.fn(),
  getEnrollmentCatalogs: vi.fn(),
}));
vi.mock("../../src/services/gradesService", () => ({
  getGradesPage: vi.fn(),
  getGradesByCourse: vi.fn(),
}));
vi.mock("../../src/services/reportsService", () => ({
  getReportsPage: vi.fn(),
  getReportsExportHistory: vi.fn(),
  downloadReportsDocument: vi.fn(),
}));
vi.mock("../../src/services/periodoService", () => ({
  listPeriodos: vi.fn(),
  markPeriodoEnviado: vi.fn(),
}));
vi.mock("../../src/services/attendanceService", () => ({
  getAttendance: vi.fn(),
  markAttendance: vi.fn(),
}));
vi.mock("../../src/services/activitiesService", () => ({
  default: {
    getActividades: vi.fn(),
    createActividad: vi.fn(),
    updateActividadesNotas: vi.fn(),
    getActividadesNotas: vi.fn(),
  },
}));

import { getCoursesPage } from "../../src/services/coursesService";
import { getCourseDetail } from "../../src/services/coursesService";
import { getAttendance } from "../../src/services/attendanceService";
import { getDocentesPage } from "../../src/services/docentesService";
import { getStudentsPage } from "../../src/services/studentsService";
import { getSchedulesPage } from "../../src/services/schedulesService";
import { getEnrollmentCatalogs } from "../../src/services/enrollmentService";
import { getGradesPage, getGradesByCourse } from "../../src/services/gradesService";
import { getReportsPage } from "../../src/services/reportsService";
import { getReportsExportHistory } from "../../src/services/reportsService";
import { listPeriodos } from "../../src/services/periodoService";
import activitiesService from "../../src/services/activitiesService";

import CursosPage from "../../src/pages/cursos/CursosPage";
import CourseDetailPage from "../../src/pages/cursos/CourseDetailPage";
import DocentesPage from "../../src/pages/docentes/DocentesPage";
import EstudiantesPage from "../../src/pages/estudiantes/EstudiantesPage";
import GradosPage from "../../src/pages/grados/GradosPage";
import HorariosPage from "../../src/pages/horarios/HorariosPage";
import EnrollmentPage from "../../src/pages/inscripcion/EnrollmentPage";
import CalificacionesPage from "../../src/pages/calificaciones/CalificacionesPage";
import ReportesPage from "../../src/pages/reportes/ReportesPage";

describe("remaining pages", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renderiza GradosPage con carga inicial", async () => {
    getGradesByCourse.mockResolvedValue({ grados: [], resumen: [] });

    render(<GradosPage />);

    expect(await screen.findByRole("heading", { name: /grados/i })).toBeInTheDocument();
    await waitFor(() => expect(getGradesByCourse).toHaveBeenCalled());
  });

  it("renderiza CursosPage con carga inicial", async () => {
    getCoursesPage.mockResolvedValue({
      resumen: [],
      cursos: [],
      permisos: { puede_crear: false },
      catalogos: { areas: [], grados: [], docentes: [] },
      paginacion: { pagina: 1, paginas: 1, anterior: false, siguiente: false, total: 0 },
    });

    render(<CursosPage />);

    expect(await screen.findByRole("heading", { name: /^cursos$/i })).toBeInTheDocument();
    await waitFor(() => expect(getCoursesPage).toHaveBeenCalled());
  });

  it("renderiza DocentesPage con carga inicial", async () => {
    getDocentesPage.mockResolvedValue({
      docentes: [],
      permisos: { puede_crear: false },
      paginacion: { pagina: 1, paginas: 1, anterior: false, siguiente: false, total: 0 },
    });

    render(<DocentesPage />);

    expect(await screen.findByRole("heading", { name: /^docentes$/i })).toBeInTheDocument();
    await waitFor(() => expect(getDocentesPage).toHaveBeenCalled());
  });

  it("renderiza EstudiantesPage con carga inicial", async () => {
    getStudentsPage.mockResolvedValue({
      resumen: [],
      estudiantes: [],
      filtros: { grados: [] },
      paginacion: { pagina: 1, paginas: 1, anterior: false, siguiente: false, total: 0 },
    });

    render(<EstudiantesPage />);

    expect(await screen.findByRole("heading", { name: /^estudiantes$/i })).toBeInTheDocument();
    await waitFor(() => expect(getStudentsPage).toHaveBeenCalled());
  });

  it("renderiza HorariosPage con carga inicial", async () => {
    getSchedulesPage.mockResolvedValue({ resumen: [], calendario: [], proximas_clases: [] });

    render(<HorariosPage />);

    expect(await screen.findByText(/horarios por clase/i)).toBeInTheDocument();
    await waitFor(() => expect(getSchedulesPage).toHaveBeenCalled());
  });

  it("renderiza EnrollmentPage y carga catalogos", async () => {
    getEnrollmentCatalogs.mockResolvedValue({ grados: [], tutores: [] });

    render(<EnrollmentPage />);

    expect(await screen.findByRole("heading", { name: /inscripción de estudiantes/i })).toBeInTheDocument();
    await waitFor(() => expect(getEnrollmentCatalogs).toHaveBeenCalled());
  });

  it("muestra las opciones de género del formulario de inscripción", async () => {
    getEnrollmentCatalogs.mockResolvedValue({ grados: [], tutores: [] });

    const { container } = render(<EnrollmentPage />);

    await act(async () => {
      await userEvent.click(screen.getByRole("button", { name: /inscripción nueva/i }));
    });
    await waitFor(() => expect(container.querySelector('select[name="genero"]')).toBeInTheDocument());
    const genderSelect = container.querySelector('select[name="genero"]');

    expect(genderSelect).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /masculino/i })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /femenino/i })).toBeInTheDocument();
  });

  it("renderiza CalificacionesPage con carga inicial", async () => {
    getGradesPage.mockResolvedValue({
      resumen: [],
      calificaciones: [],
      filtros: { periodos: [], materias: [] },
      promedio_por_asignatura: { labels: [], data: [] },
      mejores_estudiantes: [],
      por_estudiante: [],
      por_curso: [],
      permisos: { puede_crear: false, puede_ver_todo: false },
      paginacion: { pagina: 1, paginas: 1, anterior: false, siguiente: false, total: 0 },
    });

    render(<CalificacionesPage />);

    expect(await screen.findByText(/calificaciones/i)).toBeInTheDocument();
    await waitFor(() => expect(getGradesPage).toHaveBeenCalled());
  });

  it("renderiza ReportesPage con carga inicial", async () => {
    getReportsPage.mockResolvedValue({ resumen: [] });
    getReportsExportHistory.mockResolvedValue({ historico: [] });
    listPeriodos.mockResolvedValue({ periodos: [] });

    render(<ReportesPage />);

    expect(await screen.findByRole("heading", { name: /^reportes$/i })).toBeInTheDocument();
    await waitFor(() => expect(getReportsPage).toHaveBeenCalled());
  });

  it("renderiza CourseDetailPage cuando tiene asignacion", async () => {
    getCourseDetail.mockResolvedValue({ estudiantes: [] });
    activitiesService.getActividades.mockResolvedValue({ actividades: [] });

    render(
      <MemoryRouter initialEntries={["/cursos/detalle?asignacion_id=a-1"]}>
        <Routes>
          <Route path="/cursos/detalle" element={<CourseDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText(/cargando/i)).toBeInTheDocument();
    await waitFor(() => expect(getCourseDetail).toHaveBeenCalled());
  });
});