import { useState, useCallback } from 'react';
import { searchStudents } from '../../services/studentsService';
import { createLicencia } from '../../services/licenciasService';

const INITIAL_FORM = {
  estudiante_id: '',
  estudiante_nombre: '',
  motivo: '',
  fecha_inicio: '',
  fecha_fin: '',
  requiere_respaldo: false,
};

export default function CrearLicenciaModal({ onClose, onCreated }) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [query, setQuery] = useState('');
  const [sugerencias, setSugerencias] = useState([]);
  const [buscando, setBuscando] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState('');

  /* ── Búsqueda de estudiante ───────────────────────── */
  const buscarEstudiantes = useCallback(async (texto) => {
    setQuery(texto);
    setForm((f) => ({ ...f, estudiante_id: '', estudiante_nombre: '' }));
    if (texto.trim().length < 2) { setSugerencias([]); return; }
    setBuscando(true);
    try {
      const data = await searchStudents(texto);
      setSugerencias(data?.estudiantes || data?.items || []);
    } catch {
      setSugerencias([]);
    } finally {
      setBuscando(false);
    }
  }, []);

  const seleccionarEstudiante = (est) => {
    setForm((f) => ({
      ...f,
      estudiante_id: est.id,
      estudiante_nombre: `${est.nombres} ${est.primer_apellido} ${est.segundo_apellido || ''}`.trim(),
    }));
    setQuery(`${est.nombres} ${est.primer_apellido} ${est.segundo_apellido || ''}`.trim());
    setSugerencias([]);
  };

  /* ── Enviar formulario ────────────────────────────── */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!form.estudiante_id) { setError('Debes seleccionar un estudiante de la lista.'); return; }
    setGuardando(true);
    try {
      await createLicencia({
        estudiante_id: form.estudiante_id,
        motivo: form.motivo,
        fecha_inicio: form.fecha_inicio,
        fecha_fin: form.fecha_fin,
        requiere_respaldo: form.requiere_respaldo,
      });
      onCreated?.();
    } catch (err) {
      setError(err?.response?.data?.error || 'No se pudo crear la licencia.');
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg bg-white rounded-3xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-800 to-slate-700 px-6 py-4 flex items-center justify-between">
          <h2 className="text-white font-bold text-lg">📝 Nueva Licencia</h2>
          <button onClick={onClose} className="text-white/70 hover:text-white text-xl leading-none">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Buscador de estudiante */}
          <div className="relative">
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Estudiante <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => buscarEstudiantes(e.target.value)}
              placeholder="Escribe nombre o apellido..."
              className="w-full border border-slate-200 rounded-2xl px-4 py-2.5 text-sm focus:outline-none focus:border-slate-700 bg-slate-50"
              autoComplete="off"
            />
            {buscando && (
              <p className="text-xs text-slate-400 mt-1 px-1">Buscando...</p>
            )}
            {sugerencias.length > 0 && (
              <ul className="absolute z-10 w-full bg-white border border-slate-200 rounded-2xl shadow-lg mt-1 max-h-48 overflow-y-auto">
                {sugerencias.map((est) => (
                  <li key={est.id}>
                    <button
                      type="button"
                      onClick={() => seleccionarEstudiante(est)}
                      className="w-full text-left px-4 py-2.5 text-sm hover:bg-slate-50 transition"
                    >
                      <span className="font-semibold text-slate-900">
                        {est.nombres} {est.primer_apellido} {est.segundo_apellido || ''}
                      </span>
                      <span className="text-slate-400 ml-2 text-xs">{est.grado || est.curso || ''}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {form.estudiante_id && (
              <p className="text-xs text-emerald-600 mt-1 px-1 font-semibold">✔ {form.estudiante_nombre} seleccionado</p>
            )}
          </div>

          {/* Motivo */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Motivo <span className="text-rose-500">*</span>
            </label>
            <textarea
              required
              rows={3}
              value={form.motivo}
              onChange={(e) => setForm((f) => ({ ...f, motivo: e.target.value }))}
              placeholder="Ej. Enfermedad, cita médica, viaje familiar..."
              className="w-full border border-slate-200 rounded-2xl px-4 py-2.5 text-sm focus:outline-none focus:border-slate-700 bg-slate-50 resize-none"
            />
          </div>

          {/* Fechas */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Fecha inicio <span className="text-rose-500">*</span>
              </label>
              <input
                type="date"
                required
                value={form.fecha_inicio}
                onChange={(e) => setForm((f) => ({ ...f, fecha_inicio: e.target.value }))}
                className="w-full border border-slate-200 rounded-2xl px-4 py-2.5 text-sm focus:outline-none focus:border-slate-700 bg-slate-50"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Fecha fin <span className="text-rose-500">*</span>
              </label>
              <input
                type="date"
                required
                value={form.fecha_fin}
                onChange={(e) => setForm((f) => ({ ...f, fecha_fin: e.target.value }))}
                className="w-full border border-slate-200 rounded-2xl px-4 py-2.5 text-sm focus:outline-none focus:border-slate-700 bg-slate-50"
              />
            </div>
          </div>

          {/* Requiere respaldo */}
          <label className="flex items-center gap-3 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={form.requiere_respaldo}
              onChange={(e) => setForm((f) => ({ ...f, requiere_respaldo: e.target.checked }))}
              className="w-4 h-4 accent-slate-800"
            />
            <span className="text-sm font-medium text-slate-700">¿Requiere respaldo documental?</span>
          </label>

          {error && (
            <p className="text-sm text-rose-600 bg-rose-50 border border-rose-200 rounded-2xl px-4 py-2">
              {error}
            </p>
          )}

          {/* Acciones */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-2xl border border-slate-200 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={guardando}
              className="rounded-2xl bg-slate-900 px-5 py-2.5 text-sm font-bold text-white disabled:opacity-50 hover:bg-slate-700 transition"
            >
              {guardando ? 'Guardando...' : 'Crear Licencia'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
