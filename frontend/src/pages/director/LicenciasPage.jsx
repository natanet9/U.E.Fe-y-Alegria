import { useCallback, useEffect, useState } from 'react';
import { approveLicencia, getLicenciasPage } from '../../services/licenciasService';
import Toast from '../../components/Toast';

const EMPTY_ARRAY = [];

function stateStyle(estado) {
  if (estado === 'aprobada') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  if (estado === 'rechazada') return 'bg-rose-50 text-rose-700 border-rose-200';
  return 'bg-amber-50 text-amber-700 border-amber-200';
}

function LicenciasPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ mensaje: "", tipo: "success" });
  function showToast(tipo, mensaje) {
    setToast({ mensaje, tipo });
  }
  const [estado, setEstado] = useState('pendiente');
  const [page, setPage] = useState(1);
  const [busyId, setBusyId] = useState(null);
  const [observaciones, setObservaciones] = useState({});

  const loadLicencias = useCallback(() => {
    setLoading(true);
    getLicenciasPage({ estado, page, pageSize: 8 })
      .then((response) => {
        setData(response?.licencias || null);
      })
      .catch((requestError) => {
        showToast('error', requestError?.response?.data?.error || 'No fue posible cargar las licencias');
      })
      .finally(() => setLoading(false));
  }, [estado, page]);

  useEffect(() => {
    loadLicencias();
  }, [loadLicencias]);

  const licencias = data?.items || EMPTY_ARRAY;
  const totalPages = data?.paginas || data?.total_pages || 1;

  const handleAction = async (licenciaId, aceptar) => {
    setBusyId(licenciaId);
    try {
      await approveLicencia(licenciaId, {
        aceptar,
        observaciones: observaciones[licenciaId] || '',
      });
      loadLicencias();
    } catch (requestError) {
      showToast('error', requestError?.response?.data?.error || 'No fue posible procesar la licencia');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(244,114,182,0.08),rgba(255,255,255,0.94),rgba(14,165,233,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
        <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Licencias</h1>
        <p className="mt-2 max-w-2xl text-base text-slate-600">Revisa, aprueba o rechaza solicitudes desde un solo tablero.</p>
      </header>

      <div className="flex flex-wrap gap-3">
        {['pendiente', 'aprobada', 'rechazada', ''].map((option) => (
          <button
            key={option || 'todas'}
            type="button"
            onClick={() => { setEstado(option); setPage(1); }}
            className={`rounded-full border px-4 py-2 text-sm font-semibold ${estado === option ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-200 bg-white text-slate-700'}`}
          >
            {option || 'Todas'}
          </button>
        ))}
      </div>

      <Toast mensaje={toast.mensaje} tipo={toast.tipo} onClose={() => setToast({ mensaje: "", tipo: "success" })} />

      <section className="grid gap-4 lg:grid-cols-2">
        {loading ? (
          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-10 text-center text-sm text-slate-500 lg:col-span-2">Cargando licencias...</div>
        ) : licencias.length ? (
          licencias.map((licencia) => (
            <article key={licencia.id} className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-xl font-black text-slate-950">{licencia.estudiante}</h3>
                  <p className="mt-1 text-sm text-slate-500">Tutor: {licencia.tutor || '—'}</p>
                  <p className="mt-1 text-sm text-slate-500">{licencia.fecha_inicio} → {licencia.fecha_fin} · {licencia.dias} días</p>
                </div>
                <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${stateStyle(licencia.estado)}`}>{licencia.estado}</span>
              </div>

              <p className="mt-4 text-sm text-slate-600"><span className="font-semibold text-slate-900">Motivo:</span> {licencia.motivo}</p>
              <p className="mt-2 text-sm text-slate-600"><span className="font-semibold text-slate-900">Observaciones:</span> {licencia.observaciones || '—'}</p>
              <p className="mt-2 text-sm text-slate-500">Regente: {licencia.regente || '—'} · Aprobado por: {licencia.aprobado_por || '—'}</p>

              <label className="mt-4 flex flex-col gap-2 text-sm font-semibold text-slate-700">
                Observaciones para aprobación
                <textarea
                  rows={3}
                  value={observaciones[licencia.id] || ''}
                  onChange={(event) => setObservaciones((current) => ({ ...current, [licencia.id]: event.target.value }))}
                  className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none"
                />
              </label>

              <div className="mt-4 flex flex-wrap gap-2">
                <button type="button" onClick={() => handleAction(licencia.id, true)} disabled={busyId === licencia.id} className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700 disabled:opacity-50">Aprobar</button>
                <button type="button" onClick={() => handleAction(licencia.id, false)} disabled={busyId === licencia.id} className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-semibold text-rose-700 disabled:opacity-50">Rechazar</button>
              </div>
            </article>
          ))
        ) : (
          <div className="rounded-3xl border border-dashed border-slate-200 bg-slate-50 p-10 text-center text-sm text-slate-500 lg:col-span-2">No hay licencias para mostrar.</div>
        )}
      </section>

      <div className="flex items-center justify-between gap-3">
        <button type="button" disabled={page <= 1 || loading} onClick={() => setPage((current) => Math.max(current - 1, 1))} className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50">Anterior</button>
        <span className="rounded-2xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700">Página {data?.pagina || data?.page || 1} de {totalPages}</span>
        <button type="button" disabled={page >= totalPages || loading} onClick={() => setPage((current) => current + 1)} className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50">Siguiente</button>
      </div>
    </section>
  );
}

export default LicenciasPage;