"""Tests unitarios para rate limiting"""
import pytest
import time
from unittest.mock import patch
from core.rate_limit import MemoryRateLimiter, rate_limiter


class TestMemoryRateLimiter:
    """Tests para MemoryRateLimiter"""

    def test_is_allowed_first_attempt(self):
        """Verifica que la primera solicitud esté permitida"""
        limiter = MemoryRateLimiter()
        assert limiter.is_allowed("test-key") is True

    def test_is_allowed_within_limit(self):
        """Verifica que solicitudes dentro del límite estén permitidas"""
        limiter = MemoryRateLimiter()
        for i in range(5):
            assert limiter.is_allowed("test-key", max_attempts=5) is True

    def test_is_allowed_exceeds_limit(self):
        """Verifica que solicitudes excediendo el límite estén bloqueadas"""
        limiter = MemoryRateLimiter()
        for i in range(5):
            limiter.is_allowed("test-key", max_attempts=5)
        assert limiter.is_allowed("test-key", max_attempts=5) is False

    def test_is_allowed_different_keys(self):
        """Verifica que diferentes claves tengan contadores separados"""
        limiter = MemoryRateLimiter()
        for i in range(5):
            limiter.is_allowed("key1", max_attempts=5)
        assert limiter.is_allowed("key2", max_attempts=5) is True
        assert limiter.is_allowed("key1", max_attempts=5) is False

    def test_is_allowed_respects_window(self):
        """Verifica que el tiempo de ventana funcione correctamente"""
        limiter = MemoryRateLimiter()
        with patch('core.rate_limit.time.time', side_effect=[1000, 1001, 1002, 1003, 1004, 2000]):
            for i in range(5):
                limiter.is_allowed("test-key", max_attempts=5, window_seconds=500)
            # Después del tiempo de ventana, debería permitirse de nuevo
            assert limiter.is_allowed("test-key", max_attempts=5, window_seconds=500) is True

    def test_get_remaining_initial(self):
        """Verifica que get_remaining retorne el máximo inicial"""
        limiter = MemoryRateLimiter()
        assert limiter.get_remaining("test-key", max_attempts=5) == 5

    def test_get_remaining_after_attempts(self):
        """Verifica que get_remaining disminuya con intentos"""
        limiter = MemoryRateLimiter()
        limiter.is_allowed("test-key", max_attempts=5)
        assert limiter.get_remaining("test-key", max_attempts=5) == 4
        limiter.is_allowed("test-key", max_attempts=5)
        assert limiter.get_remaining("test-key", max_attempts=5) == 3

    def test_get_remaining_after_window(self):
        """Verifica que get_remaining se restablezca después del tiempo de ventana"""
        limiter = MemoryRateLimiter()
        with patch('core.rate_limit.time.time', side_effect=[1000, 2000]):
            limiter.is_allowed("test-key", max_attempts=5, window_seconds=500)
            assert limiter.get_remaining("test-key", max_attempts=5, window_seconds=500) == 5

    def test_singleton_rate_limiter(self):
        """Verifica que el singleton rate_limiter funcione correctamente"""
        assert rate_limiter is not None
        assert isinstance(rate_limiter, MemoryRateLimiter)
        assert rate_limiter.is_allowed("singleton-test") is True
