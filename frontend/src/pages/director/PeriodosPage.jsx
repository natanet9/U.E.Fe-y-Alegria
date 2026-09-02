import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  cerrarPeriodo,
  createPeriodo,
  deletePeriodo,
  habilitarPeriodo,
  listPeriodos,
  markPeriodoEnviado,
  updatePeriodo,
} from '../../services/periodoService';
import Toast from '../../components/Toast';

const EMPTY_ARRAY = [];

function StatusBadge({ periodo }) {
  const styles = {
    activo: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    cerrado: 'border-slate-200 bg-slate-100 text-slate-700',
    pendiente: 'border-amber-200 bg-amber-50 text-amber-700',
  };

  return (
    <div className="flex flex-wrap gap-2">
      <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${styles[periodo.estado] || styles.pendiente}`}>
        {periodo.estado}
      </span>
      {periodo.marcado_como_enviado ? (
        <span className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
          Enviado
        </span>
      ) : null}
    </div>
  );
}

function PeriodosPage() {
  const [periodos, setPeriodos] = useState(EMPTY_ARRAY);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState({ mensaje: '', tipo: 'success' });

  function showToast(tipo, mensaje) {
    setToast({ mensaje, tipo });
  }
  const [editId, setEditId] = useState(null);
  const [gestion, setGestion] = useState(new Date().getFullYear());
  const [formData, setFormData] = useState({
    nombre: '',
    gestion: new Date().getFullYear(),
    fecha_inicio: '',
    fecha_fin: '',
  });

  const selectedPeriod = useMemo(
    () => periodos.find((periodo) => periodo.id === editId) || null,
    [editId, periodos],
  );

  const loadPeriodos = useCallback(() => {
    setLoading(true);
    listPeriodos({ gestion })
      .then((response) => {
        const list = Array.isArray(response) ? response : (response.data || []);
        setPeriodos(list);
      })
      .catch((requestError) => {
        showToast('error', requestError?.response?.data?.error || 'No fue posible cargar los periodos');
      })
      .finally(() => setLoading(false));
  }, [gestion]);

  useEffect(() => {
    loadPeriodos();
  }, [loadPeriodos]);

  useEffect(() => {
    if (!selectedPeriod) {
      return;
    }

    setFormData({
      nombre: selectedPeriod.nombre || '',
      gestion: selectedPeriod.gestion || gestion,
      fecha_inicio: selectedPeriod.fecha_inicio || '',
      fecha_fin: selectedPeriod.fecha_fin || '',
    });
  }, [gestion, selectedPeriod]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
  };

  const resetForm = () => {
    setEditId(null);
    setFormData({
      nombre: '',
      gestion: gestion,
      fecha_inicio: '',
      fecha_fin: '',
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      if (editId) {
        await updatePeriodo(editId, formData);
        showToast('success', 'Periodo actualizado');
      } else {
        await createPeriodo(formData);
        showToast('success', 'Periodo creado');
      }
      resetForm();
      loadPeriodos();
    } catch (requestError) {
      showToast('error', requestError?.response?.data?.error || 'No fue posible guardar el periodo');
    } finally {
      setSaving(false);
    }
  };

  const handleInlineAction = async (action, periodoId) => {
    try {
      if (action === 'habilitar') {
        await habilitarPeriodo(periodoId);
        showToast('success', 'Periodo habilitado');
      }
      if (action === 'cerrar') {
        await cerrarPeriodo(periodoId);
        showToast('success', 'Periodo cerrado');
      }
      if (action === 'enviar') {
        await markPeriodoEnviado(periodoId);
        showToast('success', 'Periodo marcado como enviado');
      }
      if (action === 'eliminar') {
        await deletePeriodo(periodoId);
        showToast('success', 'Periodo eliminado');
      }
      loadPeriodos();
    } catch (requestError) {
      showToast('error', requestError?.response?.data?.error || 'No fue posible ejecutar la acción');
    }
  };

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(14,165,233,0.08),rgba(255,255,255,0.94),rgba(99,102,241,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
        <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Periodos</h1>
        <p className="mt-2 max-w-2xl text-base text-slate-600">Gestiona aperturas, cierres y el envío oficial de cada periodo académico.</p>
      </header>

      <div className="flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-sm font-semibold text-slate-600">
          Gestión
          <input
            type="number"
            value={gestion}
            onChange={(event) => setGestion(event.target.value)}
            className="w-32 rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-900 outline-none"
          />
        </label>
      </div>

      <Toast mensaje={toast.mensaje} tipo={toast.tipo} onClose={() => setToast({ mensaje: '', tipo: 'success' })} />

      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-xl font-black text-slate-950">{editId ? 'Editar periodo' : 'Crear periodo'}</h2>
            <p className="mt-1 text-sm text-slate-500">Usa este formulario para abrir o planificar nuevos trimestres.</p>
          </div>
          {editId ? <button type="button" onClick={resetForm} className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700">Cancelar edición</button> : null}
        </div>

        <form onSubmit={handleSubmit} className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
            Nombre
            <input name="nombre" value={formData.nombre} onChange={handleChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
          </label>
          <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
            Gestión
            <input name="gestion" type="number" value={formData.gestion} onChange={handleChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
          </label>
          <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
            Fecha inicio
            <input name="fecha_inicio" type="date" value={formData.fecha_inicio} onChange={handleChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
          </label>
          <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
            Fecha fin
            <input name="fecha_fin" type="date" value={formData.fecha_fin} onChange={handleChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
          </label>

          <div className="xl:col-span-4 flex flex-wrap gap-3">
            <button type="submit" disabled={saving} className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-bold text-white disabled:opacity-50">
              {saving ? 'Guardando...' : editId ? 'Actualizar periodo' : 'Crear periodo'}
            </button>
            <button type="button" onClick={resetForm} className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-bold text-slate-900">
              Limpiar
            </button>
          </div>
        </form>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        {loading ? (
          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-10 text-center text-sm text-slate-500 lg:col-span-2">Cargando periodos...</div>
        ) : periodos.length ? (
          periodos.map((periodo) => (
            <article key={periodo.id} className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <h3 className="text-xl font-black text-slate-950">{periodo.nombre}</h3>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{periodo.gestion}</span>
                  </div>
                  <p className="mt-2 text-sm text-slate-500">{periodo.fecha_inicio} → {periodo.fecha_fin}</p>
                  <p className="mt-2 text-sm text-slate-500">Habilitado por: {periodo.habilitado_por || '—'} · Cerrado por: {periodo.cerrado_por || '—'}</p>
                  <div className="mt-3"><StatusBadge periodo={periodo} /></div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <button type="button" onClick={() => setEditId(periodo.id)} className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700">Editar</button>
                  <button type="button" onClick={() => handleInlineAction('habilitar', periodo.id)} className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700">Habilitar</button>
                  <button type="button" onClick={() => handleInlineAction('cerrar', periodo.id)} className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-700">Cerrar</button>
                  <button type="button" onClick={() => handleInlineAction('enviar', periodo.id)} className="rounded-2xl border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-semibold text-blue-700">Marcar enviado</button>
                  <button type="button" onClick={() => handleInlineAction('eliminar', periodo.id)} className="rounded-2xl border border-red-200 bg-red-50 px-4 py-2 text-sm font-semibold text-red-700">Eliminar</button>
                </div>
              </div>
            </article>
          ))
        ) : (
          <div className="rounded-3xl border border-dashed border-slate-200 bg-slate-50 p-10 text-center text-sm text-slate-500 lg:col-span-2">No hay periodos para esta gestión.</div>
        )}
      </section>
    </section>
  );
}

export default PeriodosPage;