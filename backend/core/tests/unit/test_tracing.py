"""Tests para utilidades de trazabilidad"""
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from core.tracing import install_database_connection_tracing, trace_call, trace_database_connect, trace_service_class, trace_view_function, get_trace_records, _log_trace


def test_trace_call_logs_duration_and_returns_value():
    with patch("core.tracing.perf_counter", side_effect=[1.0, 1.25]), patch("core.tracing.logger.info") as logger_info:

        @trace_call("service", "demo")
        def work(value):
            return value * 2

        assert work(3) == 6

    assert logger_info.called
    assert logger_info.call_args.args[0] == "%s %s (%s ms)"


def test_trace_call_handles_exception():
    with patch("core.tracing.perf_counter", side_effect=[1.0, 1.5]), patch("core.tracing.logger.info") as logger_info:

        @trace_call("service", "demo-error")
        def failing_work():
            raise ValueError("Something went wrong")

        with pytest.raises(ValueError):
            failing_work()

    assert logger_info.called


def test_trace_service_class_wraps_public_methods():
    with patch("core.tracing.perf_counter", side_effect=[2.0, 2.5]), patch("core.tracing.logger.info") as logger_info:

        @trace_service_class
        class DemoService:
            def ping(self, value):
                return value + 1

            def _hidden(self):
                return "nope"

        assert DemoService().ping(4) == 5

    assert logger_info.called


def test_trace_view_function_preserves_return_value():
    response = SimpleNamespace(status_code=200)
    with patch("core.tracing.perf_counter", side_effect=[3.0, 3.05]), patch("core.tracing.logger.info") as logger_info:

        @trace_view_function
        def demo_view(request):
            return response

        assert demo_view(object()) is response

    assert logger_info.called


def test_trace_database_connect_wrapper_logs():
    fake_wrapper = SimpleNamespace(alias="default", settings_dict={"ENGINE": "sqlite"})

    def fake_connect(self, *args, **kwargs):
        return "connected"

    wrapped = trace_database_connect(fake_connect)

    with patch("core.tracing.perf_counter", side_effect=[4.0, 4.4]), patch("core.tracing.logger.info") as logger_info:
        result = wrapped(fake_wrapper)

    assert result == "connected"
    assert logger_info.called


def test_install_database_connection_tracing_is_idempotent(monkeypatch):
    from django.db.backends.base.base import BaseDatabaseWrapper

    original = BaseDatabaseWrapper.connect
    try:
        install_database_connection_tracing()
        first = BaseDatabaseWrapper.connect
        install_database_connection_tracing()
        second = BaseDatabaseWrapper.connect
        assert first is second
    finally:
        BaseDatabaseWrapper.connect = original


def test_get_trace_records_collects_traces():
    with patch("core.tracing.perf_counter", side_effect=[5.0, 5.5]):

        @trace_call("test", "test-function")
        def test_func():
            return "ok"

        test_func()

    records = get_trace_records()
    assert len(records) == 1
    assert records[0]["kind"] == "test"
    assert records[0]["name"] == "test-function"

    # Test clearing records
    assert get_trace_records(clear=True) == records
    assert get_trace_records() == []


def test_log_trace_handles_exceptions():
    with patch("core.tracing.TRACE_RECORDS", []):
        with patch("core.tracing.TRACE_RECORDS.append", side_effect=Exception("Append failed")):
            _log_trace("test", "error-test", 100)
    assert len(get_trace_records()) == 0