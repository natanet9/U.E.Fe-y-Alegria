import { useEffect, useState } from 'react';
import { getAsignacionesList } from '../../services/coursesService';
import Toast from '../../components/Toast';

const AREA_COLORS = [
  'from-blue-500 to-indigo-500',
  'from-emerald-500 to-teal-500', 
  'from-violet-500 to-purple-500',
  'from-amber-500 to-orange-500',
  'from-rose-500 to-pink-500',
  'from-cyan-500 to-sky-500',
];

export default function MisAreasPage() {
  const [asignaciones, setAsignaciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ mensaje: '', tipo: 'success' });

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    getAsignacionesList()
      .then(res => {
        if (mounted) {
          setAsignaciones(res || []);
        }
      })
      .catch(err => {
        if (mounted) {
          setToast({ mensaje: err?.response?.data?.error || 'Error al cargar áreas', tipo: 'error' });
          setAsignaciones([]);
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => { mounted = false; };
  }, []);

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(99,102,241,0.08),rgba(255,255,255,0.94))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-4xl font-black tracking-tight text-slate-950">Mis Áreas Asignadas</h1>
              {!loading && (
                <span className="rounded-full bg-slate-900 px-3 py-1 text-sm font-bold text-white">
                  {asignaciones.length}
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      <Toast mensaje={toast.mensaje} tipo={toast.tipo} onClose={() => setToast({ mensaje: '', tipo: 'success' })} />

      <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-48 animate-pulse rounded-[1.75rem] border border-slate-200 bg-slate-100" />
          ))
        ) : asignaciones.length > 0 ? (
          asignaciones.map((asig, idx) => {
            const colorClass = AREA_COLORS[idx % AREA_COLORS.length];
            const areaName = asig.area_nombre || asig.area || 'Área';
            const gradoName = asig.grado_nombre || asig.grado || '';
            const paraleloName = asig.paralelo_nombre || asig.paralelo || '';
            const nivelName = asig.nivel_nombre || asig.nivel || '';
            const gestion = asig.gestion;

            return (
              <article key={asig.id} className="rounded-[1.75rem] border border-slate-200 bg-white shadow-[0_18px_50px_rgba(15,23,42,0.05)] overflow-hidden transition hover:shadow-lg">
                <div className={`h-2 bg-gradient-to-r ${colorClass}`} />
                <div className="p-5">
                  <h3 className="text-2xl font-black text-slate-950">{areaName}</h3>
                  <p className="mt-1 text-sm text-slate-500 font-medium">
                    {gradoName} {paraleloName} · {nivelName}
                  </p>
                  {gestion && (
                    <span className="mt-3 inline-block rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
                      Gestión {gestion}
                    </span>
                  )}
                  
                  <div className="mt-5 grid grid-cols-2 gap-3">
                    <a
                      href={`/cursos/detalle?docente_asignacion_id=${asig.id}`}
                      className="rounded-2xl border border-slate-200 bg-white py-2.5 text-center text-sm font-bold text-slate-700 transition hover:bg-slate-50"
                    >
                      📝 Notas
                    </a>
                    <a
                      href={`/cursos/detalle?docente_asignacion_id=${asig.id}`}
                      className="rounded-2xl bg-slate-900 py-2.5 text-center text-sm font-bold text-white transition hover:bg-slate-800"
                    >
                      ✓ Asistencia
                    </a>
                  </div>
                </div>
              </article>
            );
          })
        ) : (
          <div className="sm:col-span-2 xl:col-span-3 rounded-[1.75rem] border border-dashed border-slate-200 py-12 text-center text-sm text-slate-500">
            No tienes áreas asignadas en la gestión actual
          </div>
        )}
      </div>
    </section>
  );
}
