import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import { getPadresDashboard, getBoletinEstudiante, descargarBoletinArchivo } from "../services/padresService";
import { getStoredUser } from "../services/authService";

const PadresContext = createContext(null);

export function PadresProvider({ children }) {
  const [usuario, setUsuario] = useState(() => getStoredUser());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [estudiantes, setEstudiantes] = useState([]);
  const [estudianteId, setEstudianteId] = useState(null);
  const [periodoActivo, setPeriodoActivo] = useState(null);

  // Boletín data
  const [boletin, setBoletin] = useState(null);
  const [todosBoletines, setTodosBoletines] = useState({});
  const [boletinLoading, setBoletinLoading] = useState(false);
  const [boletinError, setBoletinError] = useState("");

  // Period filter for grades view
  const [periodoSeleccionadoId, setPeriodoSeleccionadoId] = useState("todos");

  // PWA Install Prompt state
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [pwaInstallable, setPwaInstallable] = useState(false);

  // Chatbot modal/drawer
  const [chatbotOpen, setChatbotOpen] = useState(false);

  // Download state
  const [downloading, setDownloading] = useState(false);

  // PWA install handler
  useEffect(() => {
    const handleBeforeInstall = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setPwaInstallable(true);
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstall);
    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstall);
    };
  }, []);

  const promptInstallPwa = useCallback(async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === "accepted") {
      setPwaInstallable(false);
      setDeferredPrompt(null);
    }
  }, [deferredPrompt]);

  // Cargar hijos del tutor desde dashboard
  const cargarHijos = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getPadresDashboard();
      const lista = data.estudiantes || [];
      setEstudiantes(lista);
      setPeriodoActivo(data.periodo_activo || null);

      if (lista.length > 0) {
        // Cargar en segundo plano todos los boletines para el Agente IA multihijo
        lista.forEach(async (est) => {
          try {
            const b = await getBoletinEstudiante(est.id);
            setTodosBoletines((prev) => ({ ...prev, [est.id]: b }));
          } catch (_e) {}
        });

        // Restaurar selección previa si existe
        const guardado = localStorage.getItem("padres_active_child");
        const match = lista.find((e) => String(e.id) === guardado);
        const seleccionado = match ? match.id : lista[0].id;
        setEstudianteId(seleccionado);
      } else {
        setEstudianteId(null);
      }
    } catch (err) {
      setError(err?.response?.data?.error || "No se pudieron cargar los datos de tus hijos.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    cargarHijos();
  }, [cargarHijos]);

  // Cargar boletín del estudiante seleccionado
  const cargarBoletin = useCallback(async (id, gestion = "") => {
    if (!id) {
      setBoletin(null);
      return;
    }
    setBoletinLoading(true);
    setBoletinError("");
    try {
      const data = await getBoletinEstudiante(id, gestion);
      setBoletin(data);
      setTodosBoletines((prev) => ({ ...prev, [id]: data }));
      // Auto-seleccionar primer periodo o activo si no se ha seleccionado
      if (data?.periodos?.length > 0) {
        setPeriodoSeleccionadoId("todos");
      }
    } catch (err) {
      setBoletinError(err?.response?.data?.error || "No fue posible obtener el boletín de calificaciones.");
      setBoletin(null);
    } finally {
      setBoletinLoading(false);
    }
  }, []);

  useEffect(() => {
    if (estudianteId) {
      localStorage.setItem("padres_active_child", String(estudianteId));
      cargarBoletin(estudianteId);
    }
  }, [estudianteId, cargarBoletin]);

  const seleccionarEstudiante = useCallback((id) => {
    setEstudianteId(id);
  }, []);

  const estudianteActivo = useMemo(() => {
    return estudiantes.find((e) => e.id === estudianteId) || null;
  }, [estudiantes, estudianteId]);

  // Descarga de boletín oficial
  const descargarBoletin = useCallback(async (fmt = "docx") => {
    if (!estudianteId) return;
    setDownloading(true);
    try {
      const response = await descargarBoletinArchivo(estudianteId, boletin?.gestion || "", fmt);
      const mime =
        fmt === "docx"
          ? "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          : "application/pdf";
      const blob = new Blob([response.data], { type: mime });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      const nombreEstudiante = estudianteActivo
        ? `${estudianteActivo.nombres}_${estudianteActivo.primer_apellido}`.replace(/\s+/g, "_")
        : `estudiante_${estudianteId}`;
      link.download = `Boletin_${nombreEstudiante}_${boletin?.gestion || ""}.${fmt}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(err?.response?.data?.error || "Error al descargar el boletín.");
    } finally {
      setDownloading(false);
    }
  }, [estudianteId, boletin, estudianteActivo]);

  // Métricas y estadísticas calculadas del estudiante actual
  const metricas = useMemo(() => {
    if (!boletin || !boletin.materias) {
      return {
        promedioGeneral: 0,
        materiasAprobadas: 0,
        materiasReprobadas: 0,
        totalMaterias: 0,
        asistenciaPorcentaje: 0,
      };
    }

    const materias = boletin.materias || [];
    let sumaPromedios = 0;
    let materiasConNota = 0;
    let aprobadas = 0;
    let reprobadas = 0;

    materias.forEach((m) => {
      const nota = m.promedio_final != null ? Number(m.promedio_final) : null;
      if (nota != null) {
        sumaPromedios += nota;
        materiasConNota += 1;
        if (nota >= 51) {
          aprobadas += 1;
        } else {
          reprobadas += 1;
        }
      }
    });

    const promedioGeneral = materiasConNota > 0 ? (sumaPromedios / materiasConNota).toFixed(1) : "0";

    // Asistencia
    let totalClases = 0;
    let totalPresentes = 0;
    (boletin.asistencias || []).forEach((a) => {
      totalClases += a.total || 0;
      totalPresentes += a.presentes || 0;
    });
    const asistenciaPorcentaje =
      totalClases > 0 ? Math.round((totalPresentes / totalClases) * 100) : 100;

    return {
      promedioGeneral,
      materiasAprobadas: aprobadas,
      materiasReprobadas: reprobadas,
      totalMaterias: materias.length,
      asistenciaPorcentaje,
    };
  }, [boletin]);

  const value = {
    usuario,
    setUsuario,
    loading,
    error,
    estudiantes,
    estudianteId,
    estudianteActivo,
    seleccionarEstudiante,
    periodoActivo,
    boletin,
    todosBoletines,
    boletinLoading,
    boletinError,
    recargarBoletin: () => cargarBoletin(estudianteId),
    periodoSeleccionadoId,
    setPeriodoSeleccionadoId,
    metricas,
    descargarBoletin,
    downloading,
    pwaInstallable,
    promptInstallPwa,
    chatbotOpen,
    setChatbotOpen,
  };

  return <PadresContext.Provider value={value}>{children}</PadresContext.Provider>;
}

export function usePadres() {
  const context = useContext(PadresContext);
  if (!context) {
    throw new Error("usePadres debe usarse dentro de un PadresProvider");
  }
  return context;
}
