import { useEffect, useState } from "react";

export default function Toast({ mensaje, tipo = "success", onClose }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!mensaje) return;
    setVisible(true);
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(() => onClose?.(), 300);
    }, 3500);
    return () => {
      clearTimeout(timer);
      setVisible(false);
    };
  }, [mensaje, onClose]);

  if (!mensaje) return null;

  return (
    <div
      className={`fixed right-6 top-6 z-50 max-w-sm transform rounded-2xl border px-5 py-4 text-sm font-semibold shadow-2xl transition-all duration-300 ${
        visible
          ? "translate-x-0 opacity-100"
          : "translate-x-4 opacity-0"
      } ${
        tipo === "error"
          ? "border-red-200 bg-red-50 text-red-700"
          : "border-emerald-200 bg-emerald-50 text-emerald-700"
      }`}
    >
      <div className="flex items-center gap-3">
        <span className="text-lg">
          {tipo === "error" ? "✕" : "✔"}
        </span>
        <span>{mensaje}</span>
      </div>
    </div>
  );
}
