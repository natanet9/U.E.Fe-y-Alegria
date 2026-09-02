import { useEffect, useState, useCallback } from "react";
import { getDimensiones, crearDimension, actualizarDimension, eliminarDimension } from "../../services/dimensionsService";
import Toast from "../../components/Toast";

function DimensionesPage() {
  const currentYear = new Date().getFullYear();
  const [gestion, setGestion] = useState(currentYear);
  const [dimensiones, setDimensiones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ mensaje: "", tipo: "success" });
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({ nombre: "", orden: "", puntaje_maximo: "" });
  const [saving, setSaving] = useState(false);

  const showToast = useCallback((tipo, mensaje) => {
    setToast({ mensaje, tipo });
  }, []);

  const closeToast = useCallback(() => {
    setToast({ mensaje: "", tipo: "success" });
  }, []);

  const cargarDimensiones = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getDimensiones(gestion);
      setDimensiones(Array.isArray(data) ? data : data.data || []);
    } catch (err) {
      showToast("error", err?.response?.data?.error || "Error al cargar dimensiones");
    } finally {
      setLoading(false);
    }
  }, [gestion, showToast]);

  useEffect(() => {
    cargarDimensiones();
  }, [cargarDimensiones]);

  const sumaTotal = dimensiones.reduce((acc, d) => acc + (d.puntaje_maximo || 0), 0);
  const resta = 100 - sumaTotal;

  const resetForm = () => {
    setForm({ nombre: "", orden: "", puntaje_maximo: "" });
    setEditingId(null);
    setShowForm(false);
  };

  const handleEdit = (dim) => {
    setForm({
      nombre: dim.nombre,
      orden: String(dim.orden),
      puntaje_maximo: dim.puntaje_maximo != null ? String(dim.puntaje_maximo) : "",
    });
    setEditingId(dim.id);
    setShowForm(true);
  };

  const handleDelete = async (dim) => {
    if (!window.confirm(`¿Eliminar la dimensión "${dim.nombre}"?`)) return;
    try {
      await eliminarDimension(dim.id);
      showToast("success", "Dimensión eliminada");
      cargarDimensiones();
    } catch (err) {
      showToast("error", err?.response?.data?.error || "Error al eliminar");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.nombre.trim() || !form.orden) {
      showToast("error", "Debes ingresar nombre y orden");
      return;
    }

    const payload = {
      nombre: form.nombre.trim(),
      orden: parseInt(form.orden, 10),
      gestion,
    };
    if (form.puntaje_maximo !== "") {
      payload.puntaje_maximo = parseFloat(form.puntaje_maximo);
    }

    setSaving(true);
    try {
      if (editingId) {
        await actualizarDimension(editingId, payload);
        showToast("success", "Dimensión actualizada");
      } else {
        await crearDimension(payload);
        showToast("success", "Dimensión creada");
      }
      resetForm();
      cargarDimensiones();
    } catch (err) {
      showToast("error", err?.response?.data?.error || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="space-y-6">
      <Toast mensaje={toast.mensaje} tipo={toast.tipo} onClose={closeToast} />

      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(99,102,241,0.08),rgba(255,255,255,0.94),rgba(14,165,233,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
          <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Dimensiones de Evaluación</h1>
          <p className="mt-2 max-w-2xl text-base text-slate-600">
            Configura las dimensiones de evaluación y sus porcentajes para cada gestión escolar.
          </p>
        </div>
      </header>

      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_12px_40px_rgba(15,23,42,0.05)]">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Dimensiones</p>
          <p className="mt-2 text-3xl font-black text-slate-950">{dimensiones.length}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_12px_40px_rgba(15,23,42,0.05)]">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Suma de puntajes</p>
          <p className={`mt-2 text-3xl font-black ${sumaTotal > 100 ? "text-red-600" : sumaTotal === 100 ? "text-green-600" : "text-slate-950"}`}>
            {sumaTotal}%
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_12px_40px_rgba(15,23,42,0.05)]">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Por asignar</p>
          <p className={`mt-2 text-3xl font-black ${resta < 0 ? "text-red-600" : resta === 0 ? "text-green-600" : "text-amber-600"}`}>
            {resta}%
          </p>
        </div>
      </div>

      {/* Gestión selector + Add button */}
      <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <label className="text-sm font-semibold text-slate-700">Gestión:</label>
            <select
              value={gestion}
              onChange={(e) => setGestion(parseInt(e.target.value, 10))}
              className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-300"
            >
              {[currentYear - 1, currentYear, currentYear + 1].map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
          <button
            type="button"
            onClick={() => { resetForm(); setShowForm(true); }}
            className="rounded-2xl bg-blue-600 px-5 py-2.5 text-sm font-bold text-white hover:bg-blue-700 transition"
          >
            + Nueva Dimensión
          </button>
        </div>

        {/* Inline form */}
        {showForm && (
          <form onSubmit={handleSubmit} className="mt-6 rounded-2xl border border-blue-200 bg-blue-50 p-5 space-y-4">
            <p className="text-sm font-bold text-slate-900">
              {editingId ? "Editar dimensión" : "Nueva dimensión"}
            </p>
            <div className="grid gap-4 sm:grid-cols-3">
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-700">Nombre *</label>
                <input
                  type="text"
                  placeholder="Ej: Proceso, Producto, Actitud"
                  value={form.nombre}
                  onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))}
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm outline-none focus:border-blue-400"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-700">Orden *</label>
                <input
                  type="number"
                  min="1"
                  placeholder="Ej: 1, 2, 3"
                  value={form.orden}
                  onChange={(e) => setForm((f) => ({ ...f, orden: e.target.value }))}
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm outline-none focus:border-blue-400"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-700">Puntaje máximo (%)</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.01"
                  placeholder="Ej: 30"
                  value={form.puntaje_maximo}
                  onChange={(e) => setForm((f) => ({ ...f, puntaje_maximo: e.target.value }))}
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm outline-none focus:border-blue-400"
                />
              </div>
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={saving}
                className="rounded-xl bg-slate-950 px-5 py-2.5 text-sm font-bold text-white hover:bg-slate-800 disabled:opacity-50 transition"
              >
                {saving ? "Guardando..." : editingId ? "Actualizar" : "Crear"}
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-bold text-slate-700 hover:bg-slate-50 transition"
              >
                Cancelar
              </button>
            </div>
          </form>
        )}

        {/* Dimensions list */}
        <div className="mt-6">
          {loading ? (
            <p className="py-8 text-center text-sm text-slate-400">Cargando dimensiones...</p>
          ) : dimensiones.length === 0 ? (
            <p className="py-8 text-center text-sm text-slate-400">No hay dimensiones para esta gestión. Crea una nueva dimensión.</p>
          ) : (
            <div className="space-y-3">
              {dimensiones.map((dim, idx) => (
                <div
                  key={dim.id}
                  className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm hover:shadow-md transition"
                >
                  {/* Order badge */}
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-indigo-100 text-indigo-700 font-bold text-sm">
                    {dim.orden}
                  </div>

                  {/* Info */}
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-slate-900 truncate">{dim.nombre}</p>
                    <p className="text-xs text-slate-500">
                      Puntaje máximo: <span className="font-semibold text-slate-700">{dim.puntaje_maximo != null ? `${dim.puntaje_maximo}%` : "Sin definir"}</span>
                    </p>
                  </div>

                  {/* Percentage bar */}
                  {dim.puntaje_maximo != null && (
                    <div className="hidden sm:block w-32">
                      <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${dim.puntaje_maximo > 100 ? "bg-red-500" : "bg-indigo-500"}`}
                          style={{ width: `${Math.min(dim.puntaje_maximo, 100)}%` }}
                        />
                      </div>
                      <p className="mt-1 text-[10px] text-slate-400 text-center">{dim.puntaje_maximo}%</p>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => handleEdit(dim)}
                      className="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
                    >
                      Editar
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(dim)}
                      className="rounded-xl border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-600 hover:bg-red-50 transition"
                    >
                      Eliminar
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Visual percentage summary bar */}
        {dimensiones.length > 0 && (
          <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-5">
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Distribución de puntajes</p>
            <div className="flex h-6 rounded-full overflow-hidden bg-slate-200">
              {dimensiones.map((dim, idx) => {
                if (!dim.puntaje_maximo) return null;
                const colors = ["bg-indigo-500", "bg-blue-500", "bg-cyan-500", "bg-teal-500", "bg-emerald-500", "bg-violet-500", "bg-purple-500"];
                return (
                  <div
                    key={dim.id}
                    className={`${colors[idx % colors.length]} h-full transition-all`}
                    style={{ width: `${dim.puntaje_maximo}%` }}
                    title={`${dim.nombre}: ${dim.puntaje_maximo}%`}
                  />
                );
              })}
            </div>
            <div className="mt-3 flex flex-wrap gap-3">
              {dimensiones.map((dim, idx) => {
                const dotColors = ["bg-indigo-500", "bg-blue-500", "bg-cyan-500", "bg-teal-500", "bg-emerald-500", "bg-violet-500", "bg-purple-500"];
                return (
                  <div key={dim.id} className="flex items-center gap-1.5 text-xs text-slate-600">
                    <span className={`inline-block h-2.5 w-2.5 rounded-full ${dotColors[idx % dotColors.length]}`} />
                    {dim.nombre}: {dim.puntaje_maximo != null ? `${dim.puntaje_maximo}%` : "—"}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

export default DimensionesPage;