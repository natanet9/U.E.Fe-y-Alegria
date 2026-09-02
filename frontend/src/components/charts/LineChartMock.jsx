import React, { useState } from 'react';

function LineChartMock({ data = [], labels = [] , color = '#4f46e5'}) {
  const [tooltip, setTooltip] = useState(null);
  if (!data || data.length === 0) return <div className="h-full w-full flex items-center justify-center text-slate-400">Sin datos</div>;

  const width = 800;
  const height = 200;
  const padding = 20;

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const pointCoords = data.map((d, i) => {
    const x = padding + (i * (width - padding * 2)) / (data.length - 1 || 1);
    const y = padding + (1 - (d - min) / range) * (height - padding * 2);
    return { x, y };
  });

  const points = pointCoords.map(p => `${p.x},${p.y}`).join(' ');

  return (
    <div className="relative h-full w-full">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full" preserveAspectRatio="none">
        <defs>
          <linearGradient id="g" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.18" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <rect x="0" y="0" width={width} height={height} fill="transparent" />
        <polyline fill="none" stroke={color} strokeWidth="2" points={points} strokeLinecap="round" strokeLinejoin="round" />
        <polygon points={`${points} ${width - padding},${height - padding} ${padding},${height - padding}`} fill="url(#g)" />
        {pointCoords.map((p, i) => (
          <g key={i}>
            <circle cx={p.x} cy={p.y} r="6" fill="transparent" className="cursor-pointer"
              onMouseEnter={() => setTooltip({ x: p.x, y: p.y, label: labels[i], value: data[i] })}
              onMouseLeave={() => setTooltip(null)}
            />
            <circle cx={p.x} cy={p.y} r="3" fill={color} pointerEvents="none" />
          </g>
        ))}
      </svg>
      {tooltip && (
        <div className="pointer-events-none absolute z-10 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs shadow-lg"
          style={{
            left: `calc(${(tooltip.x / width) * 100}% - 40px)`,
            top: `calc(${(tooltip.y / height) * 100}% - 50px)`,
          }}>
          <p className="font-semibold text-slate-900">{tooltip.label}</p>
          <p className="text-slate-600">{tooltip.value}%</p>
        </div>
      )}
    </div>
  );
}

export default LineChartMock;
