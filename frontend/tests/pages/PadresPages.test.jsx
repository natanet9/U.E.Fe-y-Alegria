import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("../../src/services/padresService", () => ({
  getPadresDashboard: vi.fn(),
  getBoletinEstudiante: vi.fn(),
  descargarBoletinArchivo: vi.fn(),
}));

vi.mock("../../src/services/authService", () => ({
  getStoredUser: vi.fn(),
  logoutRequest: vi.fn(),
  changePasswordRequest: vi.fn(),
}));

import { getPadresDashboard, getBoletinEstudiante } from "../../src/services/padresService";
import { getStoredUser } from "../../src/services/authService";
import { PadresProvider } from "../../src/context/PadresContext";
import PadresDashboardPage from "../../src/pages/padres/PadresDashboardPage";
import PadresCalificacionesPage from "../../src/pages/padres/PadresCalificacionesPage";
import PadresAsistenciaPage from "../../src/pages/padres/PadresAsistenciaPage";
import PadresPerfilPage from "../../src/pages/padres/PadresPerfilPage";
import PadresLoginPage from "../../src/pages/padres/PadresLoginPage";

const MOCK_TUTOR = {
  id: 10,
  nombre: "Carlos",
  primer_apellido: "Mendoza",
  nombre_completo: "Carlos Mendoza Flores",
  ci: "4829104",
  email: "carlos.mendoza@gmail.com",
  rol: "tutor",
};

const MOCK_DASHBOARD = {
  estudiantes: [
    {
      id: 1,
      rude: "RUDE12345",
      nombres: "Lucas",
      primer_apellido: "Mendoza",
      segundo_apellido: "Flores",
      grado: "3ro Primaria A",
      gestion: 2026,
    },
  ],
  total_estudiantes: 1,
  periodo_activo: { id: 1, nombre: "1er Trimestre" },
};

const MOCK_BOLETIN = {
  estudiante: {
    id: 1,
    rude: "RUDE12345",
    ci: "9876543",
    nombres: "Lucas",
    primer_apellido: "Mendoza",
    segundo_apellido: "Flores",
  },
  curso: {
    id: 101,
    nombre: "3ro Primaria A",
    grado: "3ro Primaria",
    paralelo: "A",
  },
  gestion: 2026,
  periodos: [
    { id: 1, nombre: "1er Trimestre" },
    { id: 2, nombre: "2do Trimestre" },
  ],
  materias: [
    {
      docente_asignacion_id: 1,
      area_id: 1,
      area: "Matemática",
      docente: "Prof. Roberto Gomez",
      notas_por_periodo: { "1": 85, "2": 90 },
      promedio_final: 87.5,
    },
    {
      docente_asignacion_id: 2,
      area_id: 2,
      area: "Ciencias Naturales",
      docente: "Prof. Maria Suarez",
      notas_por_periodo: { "1": 45, "2": 50 },
      promedio_final: 47.5,
    },
  ],
  observaciones: [
    {
      periodo_id: 1,
      periodo: "1er Trimestre",
      area: "Matemática",
      indicador: "EA",
      observacion: "Excelente razonamiento lógico y cumplimiento oportuno.",
    },
  ],
  asistencias: [
    {
      periodo_id: 1,
      periodo: "1er Trimestre",
      total: 40,
      presentes: 38,
      porcentaje: 95,
    },
  ],
};

function renderConPadres(ui) {
  return render(
    <MemoryRouter>
      <PadresProvider>{ui}</PadresProvider>
    </MemoryRouter>
  );
}

describe("Padres Portal Pages", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getStoredUser.mockReturnValue(MOCK_TUTOR);
    getPadresDashboard.mockResolvedValue(MOCK_DASHBOARD);
    getBoletinEstudiante.mockResolvedValue(MOCK_BOLETIN);
  });

  it("PadresDashboardPage muestra el saludo al tutor y la ficha de su hijo", async () => {
    renderConPadres(<PadresDashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/Carlos/i)).toBeInTheDocument();
      expect(screen.getByText(/Lucas Mendoza/i)).toBeInTheDocument();
      expect(screen.getByText(/3ro Primaria A/i)).toBeInTheDocument();
      expect(screen.getByText("RUDE12345")).toBeInTheDocument();
    });

    // Muestra alerta si hay materias con < 51 pts (Ciencias Naturales: 47.5)
    await waitFor(() => {
      expect(screen.getByText(/Materias con puntaje menor a 51 pts/i)).toBeInTheDocument();
      expect(screen.getByText(/Ciencias Naturales/i)).toBeInTheDocument();
    });
  });

  it("PadresCalificacionesPage muestra listado de materias y notas", async () => {
    renderConPadres(<PadresCalificacionesPage />);

    await waitFor(() => {
      expect(screen.getByText(/Matemática/i)).toBeInTheDocument();
      expect(screen.getByText(/Ciencias Naturales/i)).toBeInTheDocument();
      expect(screen.getByText("87.5")).toBeInTheDocument();
      expect(screen.getByText("47.5")).toBeInTheDocument();
    });

    // Observación cualitativa docente
    expect(screen.getByText(/Excelente razonamiento lógico/i)).toBeInTheDocument();
  });

  it("PadresAsistenciaPage muestra métricas de presencia y observaciones", async () => {
    renderConPadres(<PadresAsistenciaPage />);

    await waitFor(() => {
      expect(screen.getByText(/Control de Asistencia Escolar/i)).toBeInTheDocument();
      expect(screen.getByText("95%")).toBeInTheDocument();
      expect(screen.getByText("38")).toBeInTheDocument();
    });
  });

  it("PadresPerfilPage muestra la información del tutor y la tarjeta PWA", async () => {
    renderConPadres(<PadresPerfilPage />);

    await waitFor(() => {
      expect(screen.getByText(/Carlos Mendoza Flores/i)).toBeInTheDocument();
      expect(screen.getByText("4829104")).toBeInTheDocument();
      expect(screen.getByText(/Instala el Portal en tu Celular \(PWA\)/i)).toBeInTheDocument();
    });
  });

  it("PadresLoginPage renderiza el modo de inicio asistido por Chatbot sin enlaces a docentes ni recuperacion por correo", async () => {
    getStoredUser.mockReturnValue(null);
    render(
      <MemoryRouter>
        <PadresLoginPage />
      </MemoryRouter>
    );

    expect(screen.getByText(/Asistente Escolar IA/i)).toBeInTheDocument();
    expect(screen.getByText(/Ingreso con Asistente IA/i)).toBeInTheDocument();
    expect(screen.getByText(/Formulario Rápido/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Escribe tu Carnet de Identidad \(CI\)/i)).toBeInTheDocument();

    // Comprobar aislamiento estricto: sin acceso a docentes ni enlaces de recuperacion por correo
    expect(screen.queryByText(/Acceso Docentes/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Recuperar contraseña/i })).not.toBeInTheDocument();
  });
});
