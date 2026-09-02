import React, { useState } from 'react';

const REFERENCE_LINES = [0, 25, 50, 75, 100];

function BarChartMock({ data = [], labels = [], color = '#7c3aed' }) {
  const [tooltip, setTooltip] = useState(null);
  if (!data || data.length === 0) return <div className="flex h-full w-full items-center justify-center text-slate-400">Sin datos</div>;

  const max = Math.max(...data, 1);
  const effectiveMax = Math.max(max, 25);

  return (
    <div className="relative h-full w-full">
      {/* Y-axis reference lines */}
      <div className="pointer-events-none absolute inset-0">
        {REFERENCE_LINES.filter((v) => v <= effectiveMax).map((v) => (
          <div key={v} className="absolute left-0 right-0 flex items-center" style={{ top: `${(1 - v / effectiveMax) * 100}%` }}>
            <div className="w-full border-t border-slate-200" />
            <span className="absolute -left-1 -translate-x-full text-[10px] font-medium text-slate-400">{v}%</span>
          </div>
        ))}
      </div>

      {/* Bars */}
      <div className="flex h-full items-end gap-2 pl-10">
        {data.map((d, i) => (
          <div key={i} className="relative flex flex-1 flex-col items-center justify-end h-full pb-6">
            <div
              className="w-full min-h-[4px] rounded-t-md cursor-pointer transition-all hover:opacity-80"
              style={{ height: `${(d / effectiveMax) * 100}%`, background: color, minHeight: d > 0 ? '4px' : '0' }}
              onMouseEnter={() => setTooltip({ index: i, label: labels[i], value: d })}
              onMouseLeave={() => setTooltip(null)}
            />
            <div className="absolute bottom-0 left-1/2 w-full -translate-x-1/2 truncate text-center text-[10px] text-slate-500 leading-4">
              {labels[i] || `#${i + 1}`}
            </div>
          </div>
        ))}
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="pointer-events-none absolute z-10 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs shadow-lg"
          style={{
            left: `calc(${(tooltip.index / data.length) * 100 + 50 / data.length}% - 60px)`,
            top: `calc(${(1 - tooltip.value / effectiveMax) * 100}% - 48px)`,
          }}
        >
          <p className="font-semibold text-slate-900">{tooltip.label}</p>
          <p className="text-slate-600">{tooltip.value}%</p>
        </div>
      )}
    </div>
  );
}

export default BarChartMock;