import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "../components/auth/ProtectedRoute";
import LoginPage from "../pages/auth/LoginPage";
import DashboardPage from "../pages/dashboard/DashboardPage";
import ProfilePage from "../pages/auth/ProfilePage";
import CourseDetailPage from "../pages/cursos/CourseDetailPage";
import CursosPage from "../pages/cursos/CursosPage";
import CalificacionesPage from "../pages/calificaciones/CalificacionesPage";
import EstadoNotasPage from "../pages/secretaria/EstadoNotasPage";
import DocentesPage from "../pages/docentes/DocentesPage";
import ReportesPage from "../pages/reportes/ReportesPage";
import PeriodosPage from "../pages/director/PeriodosPage";
import LicenciasPage from "../pages/director/LicenciasPage";
import GradosPage from "../pages/grados/GradosPage";
import EstudiantesPage from "../pages/estudiantes/EstudiantesPage";
import HorariosPage from "../pages/horarios/HorariosPage";
import EnrollmentPage from "../pages/inscripcion/EnrollmentPage";
import ReportCardPage from "../pages/reportes/ReportCardPage";
import UsuariosPage from "../pages/usuarios/UsuariosPage";
import DimensionesPage from "../pages/dimensiones/DimensionesPage";
import PanelAcademicoLayout from "../layouts/PanelAcademicoLayout";

function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={(
            <ProtectedRoute>
              <PanelAcademicoLayout />
            </ProtectedRoute>
          )}
        >
          <Route path="/dashboard" element={(
            <ProtectedRoute allowedRoles={["director", "secretaria", "regente", "docente", "estudiante", "tutor"]}>
              <DashboardPage />
            </ProtectedRoute>
          )} />
          <Route path="/estado-notas" element={(
            <ProtectedRoute allowedRoles={["director", "secretaria"]}>
              <EstadoNotasPage />
            </ProtectedRoute>
          )} />
          <Route path="/cursos" element={(
            <ProtectedRoute allowedRoles={["director", "secretaria", "regente", "docente"]}>
              <CursosPage />
            </ProtectedRoute>
          )} />
          <Route path="/docentes" element={(
            <ProtectedRoute allowedRoles={["director", "secretaria", "regente"]}>
              <DocentesPage />
            </ProtectedRoute>
          )} />
          <Route path="/cursos/detalle" element={(
            <ProtectedRoute allowedRoles={["director", "secretaria", "regente", "docente"]}>
              <CourseDetailPage />
            </ProtectedRoute>
          )} />
          <Route path="/perfil" element={(
            <ProtectedRoute allowedRoles={["director", "secretaria", "regente", "docente", "estudiante", "tutor"]}>
              <ProfilePage />
            </ProtectedRoute>
          )} />
          <Route path="/inscripcion" element={(
            <ProtectedRoute allowedRoles={["director", "secretaria"]}>
              <EnrollmentPage />
            </ProtectedRoute>
          )} />
          <Route path="/calificaciones" element={(
            <ProtectedRoute allowedRoles={["director", "secretaria", "regente", "docente", "estudiante"]}>
              <CalificacionesPage />
            </ProtectedRoute>
          )} />
          <Route path="/reportes" element={(
            <ProtectedRoute allowedRoles={["director", "secretaria", "regente"]}>
              <ReportesPage />
            </ProtectedRoute>
          )} />
          <Route path="/periodos" element={(
            <ProtectedRoute allowedRoles={["director"]}>
              <PeriodosPage />
            </ProtectedRoute>
          )} />
          <Route path="/licencias" element={(
            <ProtectedRoute allowedRoles={["director", "secretaria", "regente"]}>
              <LicenciasPage />
            </ProtectedRoute>
          )} />
          <Route path="/grados" element={(
            <ProtectedRoute allowedRoles={["director", "secretaria", "regente"]}>
              <GradosPage />
            </ProtectedRoute>
          )} />
          <Route path="/estudiantes" element={(
            <ProtectedRoute allowedRoles={["director", "secretaria", "regente", "docente", "tutor"]}>
              <EstudiantesPage />
            </ProtectedRoute>
          )} />
          <Route path="/horarios" element={(
            <ProtectedRoute allowedRoles={["director", "secretaria", "regente", "docente"]}>
              <HorariosPage />
            </ProtectedRoute>
          )} />
          <Route path="/boletin" element={(
            <ProtectedRoute allowedRoles={["director", "secretaria", "regente", "docente", "estudiante", "tutor"]}>
              <ReportCardPage />
            </ProtectedRoute>
          )} />
          <Route path="/usuarios" element={(
            <ProtectedRoute allowedRoles={["director"]}>
              <UsuariosPage />
            </ProtectedRoute>
          )} />
          <Route path="/dimensiones" element={(
            <ProtectedRoute allowedRoles={["director"]}>
              <DimensionesPage />
            </ProtectedRoute>
          )} />
        </Route>
        <Route
          path="*"
          element={(
            <Navigate to="/dashboard" replace />
          )}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default AppRouter;
