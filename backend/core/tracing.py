"""Utilities for timing and tracing core backend operations."""
from functools import wraps
import logging
from time import perf_counter

from django.db.backends.base.base import BaseDatabaseWrapper


logger = logging.getLogger("core.tracing")
# In-memory trace collection for tests and diagnostics
TRACE_RECORDS = []


def _log_trace(kind, name, elapsed_ms, *, status="ok", **details):
    payload = {
        "trace_kind": kind,
        "trace_name": name,
        "trace_status": status,
        "elapsed_ms": round(elapsed_ms, 2),
    }
    payload.update(details)
    try:
        # store a compact record for test-driven collection
        TRACE_RECORDS.append({
            "kind": kind,
            "name": name,
            "status": status,
            "elapsed_ms": round(elapsed_ms, 2),
            **details,
        })
    except Exception:
        # ensure tracing never breaks application flow
        pass
    logger.info("%s %s (%s ms)", kind, name, round(elapsed_ms, 2), extra=payload)


def trace_call(kind, name=None, *, extra=None):
    """Wrap a callable and log the elapsed time when it finishes."""

    def decorator(function):
        trace_name = name or function.__name__

        @wraps(function)
        def wrapper(*args, **kwargs):
            started_at = perf_counter()
            status = "ok"
            try:
                return function(*args, **kwargs)
            except Exception:
                status = "error"
                raise
            finally:
                elapsed_ms = (perf_counter() - started_at) * 1000
                details = dict(extra or {})
                _log_trace(kind, trace_name, elapsed_ms, status=status, **details)

        return wrapper

    return decorator


def trace_service_class(cls):
    """Instrument public instance methods of a service class."""
    for name, attribute in list(cls.__dict__.items()):
        if name.startswith("_") or not callable(attribute):
            continue
        setattr(cls, name, trace_call("service", f"{cls.__name__}.{name}")(attribute))
    return cls


def trace_view_function(function):
    """Instrument a DRF/Django view callable."""
    return trace_call("view", function.__name__)(function)


def trace_database_connect(connect_function):
    """Instrument a database wrapper connect method."""

    @wraps(connect_function)
    def wrapper(self, *args, **kwargs):
        started_at = perf_counter()
        try:
            return connect_function(self, *args, **kwargs)
        finally:
            elapsed_ms = (perf_counter() - started_at) * 1000
            _log_trace(
                "database",
                f"connect[{getattr(self, 'alias', 'default')}]",
                elapsed_ms,
                backend=getattr(self, "settings_dict", {}).get("ENGINE", "unknown"),
            )

    return wrapper


def install_database_connection_tracing():
    """Patch Django's database connect method once per process."""
    original_connect = BaseDatabaseWrapper.connect
    if getattr(original_connect, "_core_tracing_installed", False):
        return

    traced_connect = trace_database_connect(original_connect)
    traced_connect._core_tracing_installed = True
    BaseDatabaseWrapper.connect = traced_connect


def get_trace_records(clear=False):
    """Return collected trace records. If `clear` is True the buffer is emptied."""
    global TRACE_RECORDS
    records = list(TRACE_RECORDS)
    if clear:
        TRACE_RECORDS.clear()
    return records