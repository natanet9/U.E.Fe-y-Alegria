import { useEffect, useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getNotificaciones, marcarLeida, marcarTodasLeidas } from "../../services/notificationsService";

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Ahora";
  if (mins < 60) return `Hace ${mins} min`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `Hace ${hrs}h`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `Hace ${days}d`;
  return new Date(dateStr).toLocaleDateString("es-PA");
}

const typeStyles = {
  info: { dot: "bg-blue-500", bg: "bg-blue-50", border: "border-blue-200" },
  warning: { dot: "bg-orange-500", bg: "bg-orange-50", border: "border-orange-200" },
  alert: { dot: "bg-red-500", bg: "bg-red-50", border: "border-red-200" },
};

export default function NotificationBell() {
  const [notifications, setNotifications] = useState([]);
  const [noLeidas, setNoLeidas] = useState(0);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const ref = useRef(null);
  const navigate = useNavigate();

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getNotificaciones({ no_leidas: false, page: 1, pageSize: 20 });
      setNotifications(data.data || []);
      setNoLeidas(data.no_leidas ?? 0);
    } catch {
      // silent fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  useEffect(() => {
    if (!open) return;
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  async function handleMarkRead(id, link) {
    try {
      await marcarLeida(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, leida: true } : n))
      );
      setNoLeidas((prev) => Math.max(0, prev - 1));
      if (link) navigate(link);
    } catch {
      // silent fail
    }
  }

  async function handleMarkAllRead() {
    try {
      await marcarTodasLeidas();
      setNotifications((prev) => prev.map((n) => ({ ...n, leida: true })));
      setNoLeidas(0);
    } catch {
      // silent fail
    }
  }

  return (
    <div ref={ref} className="relative">
      <button
        title="Notificaciones"
        onClick={() => setOpen((v) => !v)}
        className="relative rounded-full p-2 text-slate-600 hover:bg-slate-100"
      >
        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 10-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h11z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M13.73 21a2 2 0 01-3.46 0" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        {noLeidas > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold leading-none text-white">
            {noLeidas > 99 ? "99+" : noLeidas}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 md:w-96">
          <div className="max-h-[28rem] overflow-y-auto rounded-2xl border border-slate-200 bg-white shadow-2xl">
            <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-100 bg-white px-4 py-3">
              <h3 className="text-sm font-bold text-slate-900">Notificaciones</h3>
              {noLeidas > 0 && (
                <button
                  onClick={handleMarkAllRead}
                  className="text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                >
                  Marcar todas leídas
                </button>
              )}
            </div>

            {loading && notifications.length === 0 ? (
              <div className="flex items-center justify-center py-10">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-200 border-t-indigo-600" />
              </div>
            ) : notifications.length === 0 ? (
              <div className="px-4 py-10 text-center text-sm text-slate-500">
                <p className="font-semibold text-slate-700">Sin notificaciones</p>
                <p className="mt-1">No tienes notificaciones nuevas.</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {notifications.map((n) => {
                  const style = typeStyles[n.tipo] || typeStyles.info;
                  return (
                    <button
                      key={n.id}
                      onClick={() => handleMarkRead(n.id, n.link)}
                      className={`flex w-full gap-3 px-4 py-3 text-left transition hover:bg-slate-50 ${
                        !n.leida ? "bg-slate-50/80" : ""
                      }`}
                    >
                      <div className={`mt-1 h-2.5 w-2.5 flex-shrink-0 rounded-full ${style.dot} ${n.leida ? "opacity-30" : ""}`} />
                      <div className="min-w-0 flex-1">
                        <p className={`text-sm ${n.leida ? "text-slate-500" : "font-semibold text-slate-900"}`}>
                          {n.mensaje}
                        </p>
                        <p className="mt-0.5 text-xs text-slate-400">{timeAgo(n.created_at)}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
