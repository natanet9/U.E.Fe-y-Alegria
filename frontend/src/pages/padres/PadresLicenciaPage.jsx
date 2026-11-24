import { useState, useEffect, useCallback } from 'react';
import { usePadres } from '../../context/PadresContext';
import { createLicencia, getMisLicencias } from '../../services/licenciasService';

const INITIAL_FORM = {
  motivo: '',
  fecha_inicio: '',
  fecha_fin: '',
  requiere_respaldo: false,
};

/* ── Helpers de UI ────────────────────────────────────── */
function estadoBadge(estado) {
  switch (estado) {
    case 'aprobada':
      return { label: '✅ Aprobada',  cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
    case 'rechazada':
      return { label: '❌ Rechazada', cls: 'bg-rose-50 text-rose-700 border-rose-200' };
    default:
      return { label: '⏳ Pendiente', cls: 'bg-amber-50 text-amber-700 border-amber-200' };
  }
}

function LicenciaCard({ licencia }) {
  const badge = estadoBadge(licencia.estado);
  return (
    <div className="bg-white rounded-3xl border border-slate-200 p-4 shadow-sm space-y-2">
      {/* Cabecera */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-bold text-slate-900 leading-tight">{licencia.estudiante}</p>
          <p className="text-xs text-slate-500 mt-0.5">
            {licencia.fecha_inicio} → {licencia.fecha_fin}
            {licencia.dias ? ` · ${licencia.dias} día${licencia.dias !== 1 ? 's' : ''}` : ''}
          </p>
        </div>
        <span className={`shrink-0 rounded-full border px-2.5 py-0.5 text-[11px] font-bold ${badge.cls}`}>
          {badge.label}
        </span>
      </div>

      {/* Motivo */}
      <p className="text-xs text-slate-600">
        <span className="font-semibold text-slate-800">Motivo:</span> {licencia.motivo}
      </p>

      {/* Observaciones del colegio (solo si hay) */}
      {licencia.observaciones && (
        <div className="rounded-2xl bg-slate-50 border border-slate-200 px-3 py-2 text-xs text-slate-700">
          <span className="font-semibold">Observación del colegio:</span> {licencia.observaciones}
        </div>
      )}

      {/* Aprobado por */}
      {licencia.aprobado_por && (
        <p className="text-[11px] text-slate-400">
          Resuelto por <span className="font-semibold">{licencia.aprobado_por}</span>
          {licencia.aprobado_en ? ` el ${licencia.aprobado_en.slice(0, 10)}` : ''}
        </p>
      )}

      {/* Respaldo */}
      {licencia.requiere_respaldo && (
        <p className={`text-[11px] font-semibold ${licencia.respaldo_presentado ? 'text-emerald-600' : 'text-amber-600'}`}>
          {licencia.respaldo_presentado ? '📎 Respaldo presentado' : '📎 Respaldo pendiente de entrega'}
        </p>
      )}
    </div>
  );
}

/* ── Página principal ─────────────────────────────────── */
function PadresLicenciaPage() {
  const { estudiantes, estudianteActivo, seleccionarEstudiante } = usePadres();

  // Formulario de nueva solicitud
  const [form, setForm]       = useState(INITIAL_FORM);
  const [guardando, setGuardando] = useState(false);
  const [exito, setExito]     = useState(false);
  const [errorForm, setErrorForm] = useState('');

  // Historial de licencias
  const [licencias, setLicencias]   = useState([]);
  const [cargando, setCargando]     = useState(true);
  const [errorHist, setErrorHist]   = useState('');

  const cargarLicencias = useCallback(() => {
    setCargando(true);
    setErrorHist('');
    getMisLicencias({ pageSize: 50 })
      .then((data) => {
        const items = data?.licencias?.items || data?.items || [];
        setLicencias(items);
      })
      .catch(() => setErrorHist('No se pudieron cargar tus solicitudes anteriores.'))
      .finally(() => setCargando(false));
  }, []);

  useEffect(() => { cargarLicencias(); }, [cargarLicencias]);

  // Filtrar historial por estudiante activo (opcional, muestra todas si no hay filtro)
  const historialFiltrado = estudianteActivo?.id
    ? licencias.filter((l) => l.estudiante_id === estudianteActivo.id)
    : licencias;

  /* ── Envío de formulario ── */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorForm('');
    if (!estudianteActivo?.id) {
      setErrorForm('Debes seleccionar a tu hijo/a para solicitar la licencia.');
      return;
    }
    setGuardando(true);
    try {
      await createLicencia({
        estudiante_id: estudianteActivo.id,
        motivo: form.motivo,
        fecha_inicio: form.fecha_inicio,
        fecha_fin: form.fecha_fin,
        requiere_respaldo: form.requiere_respaldo,
      });
      setExito(true);
      setForm(INITIAL_FORM);
      cargarLicencias(); // actualiza el historial inmediatamente
    } catch (err) {
      setErrorForm(err?.response?.data?.error || 'No se pudo enviar la solicitud. Intenta de nuevo.');
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div className="space-y-5 pb-6">

      {/* ── Encabezado ── */}
      <div className="rounded-3xl bg-gradient-to-br from-red-600 to-rose-700 p-5 text-white shadow-lg shadow-red-500/20">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-white/20 flex items-center justify-center text-2xl">📋</div>
          <div>
            <h1 className="font-bold text-lg leading-tight">Licencias</h1>
            <p className="text-xs text-rose-200 mt-0.5">Portal de Familias · U.E. Fe y Alegría</p>
          </div>
        </div>
        <p className="mt-3 text-sm text-rose-100 leading-relaxed">
          Solicita permisos de ausencia y consulta el estado de tus solicitudes anteriores.
        </p>
      </div>

      {/* ── Selector de hijo (si hay más de uno) ── */}
      {estudiantes && estudiantes.length > 1 && (
        <div className="bg-white rounded-3xl border border-slate-200 p-4 shadow-sm">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">¿Para cuál hijo/a?</p>
          <div className="flex flex-wrap gap-2">
            {estudiantes.map((est) => (
              <button
                key={est.id}
                type="button"
                onClick={() => seleccionarEstudiante(est.id)}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition ${
                  estudianteActivo?.id === est.id
                    ? 'bg-red-600 text-white border-red-600 shadow-sm'
                    : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
                }`}
              >
                {est.nombres} {est.primer_apellido}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Historial de solicitudes ── */}
      <div className="space-y-3">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-sm font-bold text-slate-800">📂 Mis solicitudes</h2>
          <button
            type="button"
            onClick={cargarLicencias}
            className="text-xs text-slate-500 hover:text-red-600 transition font-semibold"
          >
            🔄 Actualizar
          </button>
        </div>

        {cargando ? (
          <div className="bg-white rounded-3xl border border-slate-200 p-6 text-center text-sm text-slate-400 shadow-sm">
            Cargando solicitudes...
          </div>
        ) : errorHist ? (
          <div className="bg-rose-50 rounded-3xl border border-rose-200 p-4 text-xs text-rose-700 text-center">
            {errorHist}
          </div>
        ) : historialFiltrado.length === 0 ? (
          <div className="bg-white rounded-3xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-400 shadow-sm">
            No tienes solicitudes de licencia registradas aún.
          </div>
        ) : (
          <div className="space-y-3">
            {/* Resumen rápido de estados */}
            <div className="grid grid-cols-3 gap-2">
              {[
                { label: 'Pendientes', estado: 'pendiente', color: 'bg-amber-50 border-amber-200 text-amber-700' },
                { label: 'Aprobadas',  estado: 'aprobada',  color: 'bg-emerald-50 border-emerald-200 text-emerald-700' },
                { label: 'Rechazadas', estado: 'rechazada', color: 'bg-rose-50 border-rose-200 text-rose-700' },
              ].map(({ label, estado, color }) => {
                const count = historialFiltrado.filter((l) => l.estado === estado).length;
                return (
                  <div key={estado} className={`rounded-2xl border p-3 text-center ${color}`}>
                    <p className="text-xl font-black">{count}</p>
                    <p className="text-[10px] font-semibold uppercase tracking-wide mt-0.5">{label}</p>
                  </div>
                );
              })}
            </div>

            {/* Tarjetas de licencias */}
            {historialFiltrado.map((lic) => (
              <LicenciaCard key={lic.id} licencia={lic} />
            ))}
          </div>
        )}
      </div>

      {/* ── Formulario nueva solicitud ── */}
      <div className="space-y-3">
        <h2 className="text-sm font-bold text-slate-800 px-1">➕ Nueva solicitud</h2>

        {exito ? (
          <div className="bg-white rounded-3xl border border-emerald-200 p-6 text-center shadow-sm space-y-3">
            <div className="text-5xl">✅</div>
            <h3 className="font-bold text-base text-slate-900">¡Solicitud enviada!</h3>
            <p className="text-sm text-slate-500">
              Tu solicitud para <strong>{estudianteActivo?.nombres}</strong> está <strong>pendiente de revisión</strong>.
              Puedes ver su estado arriba en "Mis solicitudes".
            </p>
            <button
              type="button"
              onClick={() => setExito(false)}
              className="inline-block rounded-2xl border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Enviar otra solicitud
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="bg-white rounded-3xl border border-slate-200 p-5 shadow-sm space-y-4">
            {/* Estudiante activo */}
            <div className="flex items-center gap-3 p-3 rounded-2xl bg-slate-50 border border-slate-200">
              <div className="w-9 h-9 rounded-xl bg-red-100 flex items-center justify-center text-red-600 font-bold text-sm flex-shrink-0">
                {estudianteActivo?.nombres?.[0] || '?'}
              </div>
              <div>
                <p className="text-sm font-bold text-slate-900">
                  {estudianteActivo
                    ? `${estudianteActivo.nombres} ${estudianteActivo.primer_apellido || ''}`
                    : 'Sin estudiante seleccionado'}
                </p>
                {estudianteActivo?.grado && (
                  <p className="text-xs text-slate-500">{estudianteActivo.grado}</p>
                )}
              </div>
            </div>

            {/* Motivo */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                Motivo de ausencia <span className="text-rose-500">*</span>
              </label>
              <textarea
                required
                rows={3}
                value={form.motivo}
                onChange={(e) => setForm((f) => ({ ...f, motivo: e.target.value }))}
                placeholder="Ej: Cita médica, enfermedad, viaje familiar..."
                className="w-full border border-slate-200 rounded-2xl px-4 py-3 text-sm bg-slate-50 focus:outline-none focus:border-red-400 resize-none transition"
              />
            </div>

            {/* Fechas */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                  Desde <span className="text-rose-500">*</span>
                </label>
                <input
                  type="date"
                  required
                  value={form.fecha_inicio}
                  onChange={(e) => setForm((f) => ({ ...f, fecha_inicio: e.target.value }))}
                  className="w-full border border-slate-200 rounded-2xl px-3 py-2.5 text-sm bg-slate-50 focus:outline-none focus:border-red-400 transition"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                  Hasta <span className="text-rose-500">*</span>
                </label>
                <input
                  type="date"
                  required
                  value={form.fecha_fin}
                  onChange={(e) => setForm((f) => ({ ...f, fecha_fin: e.target.value }))}
                  className="w-full border border-slate-200 rounded-2xl px-3 py-2.5 text-sm bg-slate-50 focus:outline-none focus:border-red-400 transition"
                />
              </div>
            </div>

            {/* Requiere respaldo */}
            <label className="flex items-center gap-3 cursor-pointer p-3 rounded-2xl bg-slate-50 border border-slate-200 select-none">
              <input
                type="checkbox"
                checked={form.requiere_respaldo}
                onChange={(e) => setForm((f) => ({ ...f, requiere_respaldo: e.target.checked }))}
                className="w-4 h-4 accent-red-600"
              />
              <span className="text-sm text-slate-700">Adjuntaré documentación de respaldo (receta, certificado, etc.)</span>
            </label>

            {/* Aviso */}
            <div className="flex gap-2 p-3 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-800">
              <span>⚠️</span>
              <p>Esta solicitud será revisada por el personal de la institución. Puedes ver el estado en "Mis solicitudes".</p>
            </div>

            {errorForm && (
              <p className="text-sm text-rose-600 bg-rose-50 border border-rose-200 rounded-2xl px-4 py-2.5">
                ⚠️ {errorForm}
              </p>
            )}

            <button
              type="submit"
              disabled={guardando}
              className="w-full rounded-2xl bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-bold py-3 text-sm transition active:scale-95 shadow-sm"
            >
              {guardando ? 'Enviando solicitud...' : '📋 Enviar Solicitud de Licencia'}
            </button>
          </form>
        )}
      </div>

      {/* ── Aviso chatbot ── */}
      <div className="bg-white rounded-3xl border border-slate-200 p-4 shadow-sm flex items-start gap-3">
        <span className="text-2xl flex-shrink-0">🤖</span>
        <div>
          <p className="text-sm font-bold text-slate-900 mb-0.5">¿Necesitas ayuda?</p>
          <p className="text-xs text-slate-500">
            Usa el <strong>Chatbot IA</strong> (botón rojo flotante) para solicitar una licencia por voz o consultar el estado de las solicitudes anteriores.
          </p>
        </div>
      </div>

    </div>
  );
}

export default PadresLicenciaPage;
