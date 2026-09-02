function PieChartMock({ segments = [], title = "Distribución", totalStudents = 0 }) {
  const totalSum = segments.reduce((sum, segment) => sum + (segment.value || 0), 0) || 1;

  let accumulated = 0;
  const stops = segments.map((segment) => {
    const start = accumulated;
    const end = accumulated + (segment.value / totalSum) * 100;
    accumulated = end;
    return `${segment.color || "#6366f1"} ${start}% ${end}%`;
  });

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_0.9fr] lg:items-center">
      <div className="relative mx-auto flex h-56 w-56 items-center justify-center rounded-full p-3">
        <div
          className="absolute inset-0 rounded-full"
          style={{ background: stops.length ? `conic-gradient(${stops.join(", ")})` : "#e2e8f0" }}
        />
        <div className="absolute inset-10 rounded-full border border-white bg-white shadow-sm" />
        <div className="relative z-10 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">{title}</p>
          <p className="mt-2 text-3xl font-black text-slate-900">{totalStudents || totalSum}</p>
          <p className="mt-1 text-sm text-slate-500">{totalStudents ? "estudiantes" : "%"}</p>
        </div>
      </div>

      <div className="space-y-3">
        {segments.map((segment) => (
          <div key={segment.label} className="flex items-center justify-between gap-4 rounded-2xl bg-slate-50 px-4 py-3">
            <div className="flex items-center gap-3">
              <span className="h-3 w-3 rounded-full" style={{ backgroundColor: segment.color || "#6366f1" }} />
              <div>
                <p className="text-sm font-semibold text-slate-900">{segment.label}</p>
                <p className="text-xs text-slate-500">{segment.description || "Distribución académica"}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-bold text-slate-900">{segment.value}%</p>
              {totalStudents > 0 && (
                <p className="text-xs text-slate-400">{Math.round(totalStudents * segment.value / 100)} estudiantes</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default PieChartMock;
