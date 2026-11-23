import React, { useState, useEffect, useCallback } from "react";
import { listarTutores, generarCredencialesTutor } from "../../services/tutoresService";
import Toast from "../../components/Toast";
import Modal from "../../components/Modal";

export default function TutoresPage() {
  const [tutores, setTutores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [busquedaInput, setBusquedaInput] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  // Modal de confirmación previa
  const [tutorAConfirmar, setTutorAConfirmar] = useState(null);

  // Modal de credenciales generadas/restablecidas
  const [credencialModalOpen, setCredencialModalOpen] = useState(false);
  const [credencialData, setCredencialData] = useState(null);
  const [copiado, setCopiado] = useState(false);
  const [procesandoId, setProcesandoId] = useState(null);

  const [toast, setToast] = useState({ mensaje: "", tipo: "success" });
  const showToast = useCallback((tipo, mensaje) => setToast({ mensaje, tipo }), []);

  const cargarTutores = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listarTutores({ query, page, pageSize: 12 });
      if (data && Array.isArray(data.data)) {
        setTutores(data.data);
        setTotal(data.total || data.data.length);
        setTotalPages(data.total_pages || 1);
      } else if (Array.isArray(data)) {
        setTutores(data);
        setTotal(data.length);
        setTotalPages(1);
      }
    } catch (err) {
      showToast("error", err?.response?.data?.error || "Error al cargar tutores");
    } finally {
      setLoading(false);
    }
  }, [query, page, showToast]);

  useEffect(() => {
    cargarTutores();
  }, [cargarTutores]);

  const handleBuscar = (e) => {
    e.preventDefault();
    setQuery(busquedaInput.trim());
    setPage(1);
  };

  const handleLimpiarBusqueda = () => {
    setBusquedaInput("");
    setQuery("");
    setPage(1);
  };

  const handleRestablecerContrasena = async (tutor) => {
    setProcesandoId(tutor.id);
    try {
      const resp = await generarCredencialesTutor(tutor.id);
      setCredencialData({
        nombre: tutor.nombre_completo || `${tutor.nombres} ${tutor.primer_apellido}`,
        ci: resp.ci || tutor.ci,
        usuario: resp.usuario || tutor.ci,
        password_temporal: resp.password_temporal || "123456",
        es_nuevo: !tutor.tiene_usuario,
      });
      setCopiado(false);
      setCredencialModalOpen(true);
      showToast("success", tutor.tiene_usuario ? "Contraseña restablecida con éxito" : "Cuenta creada con éxito");
      cargarTutores();
    } catch (err) {
      showToast("error", err?.response?.data?.error || "No se pudo restablecer la contraseña");
    } finally {
      setProcesandoId(null);
    }
  };

  const handleCopiarCredenciales = () => {
    if (!credencialData) return;
    const texto = `U.E. Fe y Alegría - Credenciales de Acceso al Portal de Padres\n\nTutor: ${credencialData.nombre}\nUsuario / CI: ${credencialData.ci}\nContraseña Temporal: ${credencialData.password_temporal}\n\nIngreso en: http://localhost:3000/padres/login`;
    navigator.clipboard.writeText(texto).then(() => {
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    });
  };

  return (
    <div className="space-y-6">
      {toast.mensaje && (
        <Toast
          type={toast.tipo}
          message={toast.mensaje}
          onClose={() => setToast({ mensaje: "", tipo: "success" })}
        />
      )}

      {/* Cabecera */}
      <div className="bg-white rounded-2xl p-6 shadow-xs border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">👨‍👩‍👧‍👦</span>
            <h1 className="text-2xl font-bold text-slate-800">
              Gestión y Acceso de Padres de Familia
            </h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Módulo oficial para Dirección y Secretaría: soporte presencial, restablecimiento de contraseñas y asignación de credenciales a la PWA móvil.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold px-3 py-1.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
            Total Tutores: {total}
          </span>
        </div>
      </div>

      {/* Barra de Filtros y Búsqueda */}
      <div className="bg-white rounded-2xl p-4 shadow-xs border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
        <form onSubmit={handleBuscar} className="flex-1 flex gap-2 w-full sm:max-w-md">
          <input
            type="text"
            value={busquedaInput}
            onChange={(e) => setBusquedaInput(e.target.value)}
            placeholder="Buscar por CI, nombre o apellido del tutor..."
            className="flex-1 bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:bg-white transition"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl text-sm transition shrink-0"
          >
            Buscar
          </button>
          {query && (
            <button
              type="button"
              onClick={handleLimpiarBusqueda}
              className="px-3 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-xl text-xs font-semibold transition"
            >
              Limpiar
            </button>
          )}
        </form>

        <span className="text-xs text-slate-400 self-end sm:self-center">
          Página {page} de {totalPages}
        </span>
      </div>

      {/* Tabla de Tutores */}
      <div className="bg-white rounded-2xl shadow-xs border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500 text-sm">
            Cargando directorio de tutores...
          </div>
        ) : tutores.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            No se encontraron tutores con los criterios de búsqueda.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600 text-xs uppercase font-bold border-b border-slate-200">
                <tr>
                  <th className="px-5 py-3.5">Cédula de Identidad (CI)</th>
                  <th className="px-5 py-3.5">Nombre Completo</th>
                  <th className="px-5 py-3.5">Hijos / Estudiantes Vinculados</th>
                  <th className="px-5 py-3.5">Contacto</th>
                  <th className="px-5 py-3.5 text-center">Estado de Cuenta</th>
                  <th className="px-5 py-3.5 text-right">Acción de Acceso</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {tutores.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50/80 transition">
                    <td className="px-5 py-4 font-mono font-bold text-slate-800">
                      <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-xs">
                        {t.ci}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <div className="font-semibold text-slate-900">{t.nombre_completo || `${t.nombres} ${t.primer_apellido}`}</div>
                      <span className="text-xs text-slate-400">{t.parentesco || "Tutor"}</span>
                    </td>
                    <td className="px-5 py-4">
                      {t.estudiantes && t.estudiantes.length > 0 ? (
                        <div className="flex flex-wrap gap-1.5 max-w-xs">
                          {t.estudiantes.map((hijo) => (
                            <span
                              key={hijo.id}
                              className="text-[11px] font-medium bg-red-50 text-red-700 border border-red-100 px-2 py-0.5 rounded-full"
                            >
                              👶 {hijo.nombre_completo} ({hijo.curso})
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-xs text-slate-400 italic">Sin hijos asignados</span>
                      )}
                    </td>
                    <td className="px-5 py-4 text-xs text-slate-600">
                      <div>📞 {t.celular || "Sin celular"}</div>
                      {t.email && <div className="text-[11px] text-slate-400 truncate max-w-[180px]">✉️ {t.email}</div>}
                    </td>
                    <td className="px-5 py-4 text-center">
                      {t.tiene_usuario ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                          <span>Cuenta Activa</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-1 rounded-full bg-slate-100 text-slate-500 border border-slate-200">
                          <span>Sin Cuenta</span>
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-4 text-right">
                      <button
                        onClick={() => setTutorAConfirmar(t)}
                        disabled={procesandoId === t.id}
                        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition shadow-2xs ${
                          t.tiene_usuario
                            ? "bg-amber-500 hover:bg-amber-600 text-white"
                            : "bg-blue-600 hover:bg-blue-700 text-white"
                        }`}
                        title="Generar nueva contraseña temporal para el padre de familia"
                      >
                        {procesandoId === t.id ? (
                          <span>Procesando...</span>
                        ) : t.tiene_usuario ? (
                          <>
                            <span>🔑</span>
                            <span>Restablecer Clave</span>
                          </>
                        ) : (
                          <>
                            <span>➕</span>
                            <span>Crear Acceso</span>
                          </>
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Paginador */}
        {totalPages > 1 && (
          <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-100 disabled:opacity-40 transition"
            >
              Anterior
            </button>
            <span className="text-slate-600">
              Página {page} de {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-100 disabled:opacity-40 transition"
            >
              Siguiente
            </button>
          </div>
        )}
      </div>

      {/* Modal de Confirmación Previo */}
      <Modal
        isOpen={Boolean(tutorAConfirmar)}
        mode="confirm"
        iconType="warning"
        title={tutorAConfirmar?.tiene_usuario ? "Restablecer Contraseña" : "Crear Cuenta de Tutor"}
        message={
          tutorAConfirmar
            ? `¿Está seguro de ${
                tutorAConfirmar.tiene_usuario
                  ? "restablecer la contraseña"
                  : "crear la cuenta de acceso"
              } para ${
                tutorAConfirmar.nombre_completo ||
                `${tutorAConfirmar.nombres} ${tutorAConfirmar.primer_apellido}`
              } (CI: ${tutorAConfirmar.ci})? Se generará una contraseña temporal para entrega presencial.`
            : ""
        }
        confirmLabel={tutorAConfirmar?.tiene_usuario ? "Sí, Restablecer" : "Sí, Crear Cuenta"}
        cancelLabel="Cancelar"
        onConfirm={async () => {
          const tutor = tutorAConfirmar;
          setTutorAConfirmar(null);
          if (tutor) {
            await handleRestablecerContrasena(tutor);
          }
        }}
        onCancel={() => setTutorAConfirmar(null)}
      />

      {/* Modal de Entrega de Credenciales Temporales */}
      {credencialModalOpen && credencialData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 animate-in fade-in duration-150">
          <div className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl border border-slate-100">
            <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
              <div className="w-12 h-12 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center text-2xl font-bold">
                🔑
              </div>
              <div className="flex-1">
                <span className="text-[11px] font-bold uppercase tracking-wider text-amber-600 bg-amber-50 px-2.5 py-0.5 rounded-full">
                  {credencialData.es_nuevo ? "Nueva Cuenta Creada" : "Contraseña Restablecida"}
                </span>
                <h3 className="text-lg font-black text-slate-900 mt-1">
                  Credenciales de Acceso para el Tutor
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setCredencialModalOpen(false)}
                className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 flex items-center justify-center font-bold text-sm transition"
              >
                ✕
              </button>
            </div>

            <div className="mt-4 p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-3">
              <p className="text-xs text-slate-600">
                Entregue estas credenciales en persona al padre/madre de familia para su ingreso al portal móvil:
              </p>
              <div className="bg-white rounded-xl p-3 border border-slate-200 text-sm space-y-2">
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span>Tutor(a):</span>
                  <span className="font-semibold text-slate-900 text-sm">{credencialData.nombre}</span>
                </div>
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span>Usuario / C.I.:</span>
                  <span className="font-mono font-bold text-slate-900 text-base">{credencialData.ci}</span>
                </div>
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span>Contraseña Temporal:</span>
                  <span className="font-mono font-bold text-emerald-700 text-base bg-emerald-50 px-2.5 py-0.5 rounded">
                    {credencialData.password_temporal}
                  </span>
                </div>
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span>Portal Web Móvil:</span>
                  <span className="text-blue-600 font-medium">/padres/login</span>
                </div>
              </div>

              <div className="rounded-xl bg-amber-50 border border-amber-200 p-3 text-xs text-amber-800 flex items-start gap-2">
                <span className="text-base">⚠️</span>
                <span>
                  Por políticas de seguridad, no se envían correos de recuperación. Al iniciar sesión por primera vez con su C.I. y esta contraseña, el sistema le solicitará definir una contraseña personal.
                </span>
              </div>
            </div>

            <div className="mt-5 flex gap-2 justify-end">
              <button
                type="button"
                onClick={handleCopiarCredenciales}
                className="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50 flex items-center gap-1.5 transition"
              >
                {copiado ? "✓ ¡Copiado!" : "📋 Copiar Ficha"}
              </button>
              <button
                type="button"
                onClick={() => window.print()}
                className="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50 flex items-center gap-1.5 transition"
              >
                🖨️ Imprimir
              </button>
              <button
                type="button"
                onClick={() => setCredencialModalOpen(false)}
                className="rounded-xl bg-slate-900 px-5 py-2.5 text-xs font-bold text-white hover:bg-slate-800 transition"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
