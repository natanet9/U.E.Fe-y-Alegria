import { useEffect, useState } from "react";

const ICONS = {
  warning: { emoji: "⚠️", bg: "bg-amber-100 text-amber-600" },
  delete: { emoji: "🗑️", bg: "bg-red-100 text-red-600" },
  info: { emoji: "ℹ️", bg: "bg-blue-100 text-blue-600" },
  success: { emoji: "✅", bg: "bg-emerald-100 text-emerald-600" },
};

export default function Modal({ isOpen, mode = "confirm", iconType = "info", title, message, inputPlaceholder, inputValue: initialInput, onConfirm, onCancel, confirmLabel = "Aceptar", cancelLabel = "Cancelar" }) {
  const [input, setInput] = useState(initialInput || "");

  useEffect(() => {
    if (isOpen) setInput(initialInput || "");
  }, [isOpen, initialInput]);

  const icon = ICONS[iconType] || ICONS.info;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-md transform rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl transition-all">
        <div className="flex flex-col items-center text-center">
          <div className={`flex h-14 w-14 items-center justify-center rounded-full text-2xl ${icon.bg}`}>
            {icon.emoji}
          </div>
          {title && <h3 className="mt-4 text-lg font-bold text-slate-950">{title}</h3>}
          <p className="mt-2 text-sm text-slate-600">{message}</p>
        </div>

        {mode === "prompt" && (
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={inputPlaceholder || ""}
            className="mt-4 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white"
            autoFocus
          />
        )}

        <div className="mt-6 flex gap-3">
          <button type="button" onClick={onCancel} className="flex-1 rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
            {cancelLabel}
          </button>
          <button type="button" onClick={() => onConfirm(mode === "prompt" ? input : undefined)} className="flex-1 rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800">
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}