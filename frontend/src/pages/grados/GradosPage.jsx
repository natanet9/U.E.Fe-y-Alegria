import { useEffect, useState } from "react";
import { getGradesByCourse } from "../../services/gradesService";
import Toast from "../../components/Toast";

const EMPTY_ARRAY = [];

function GradosPage() {
  const [data, setData] = useState(null);
  const [toast, setToast] = useState({ mensaje: "", tipo: "success" });
  function showToast(tipo, mensaje) {
    setToast({ mensaje, tipo });
  }

  useEffect(() => {
    let mounted = true;

    getGradesByCourse()
      .then((response) => {
        if (!mounted) return;
        setData(response);
      })
      .catch((requestError) => {
        if (!mounted) return;
        showToast("error", requestError?.response?.data?.error || "No fue posible cargar los grados");
      });

    return () => { mounted = false; };
  }, []);

  const grados = data?.grados || EMPTY_ARRAY;
  const resumen = data?.resumen || EMPTY_ARRAY;

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(14,165,233,0.08),rgba(255,255,255,0.94),rgba(99,102,241,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
            <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Grados</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">Resumen de rendimiento por nivel escolar.</p>
          </div>
        </div>
      </header>

      <Toast mensaje={toast.mensaje} tipo={toast.tipo} onClose={() => setToast({ mensaje: "", tipo: "success" })} />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {grados.length
          ? grados.map((item, index) => (
              <article key={item.id || item.grado || item.nombre || index} className="rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-cyan-50 p-5">
                <p className="text-sm font-medium text-slate-500">{item.nombre || item.grado}</p>
                <p className="mt-1 text-2xl font-bold text-slate-900">{item.estudiantes || item.total_estudiantes || 0} estudiantes</p>
                <p className="mt-2 text-sm text-slate-700">Promedio general: {item.promedio || item.promedio_general || "-"}</p>
              </article>
            ))
          : <div className="rounded-3xl border border-slate-200 bg-slate-50 p-10 text-center text-sm text-slate-500 lg:col-span-3">No hay grados para mostrar.</div>}
      </div>

      {resumen.length ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <h2 className="text-xl font-black text-slate-950">Resumen</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {resumen.map((item) => (
              <div key={item.titulo} className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-500">{item.titulo}</p>
                <p className="mt-1 text-2xl font-bold text-slate-900">{item.valor}</p>
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </section>
  );
}

export default GradosPage;
