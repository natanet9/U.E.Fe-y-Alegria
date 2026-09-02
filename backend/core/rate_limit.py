import time
from collections import defaultdict
from threading import Lock


class MemoryRateLimiter:
    """Simple in-memory rate limiter. Not for multi-process deployment."""

    def __init__(self):
        self._attempts = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str, max_attempts: int = 5, window_seconds: int = 300) -> bool:
        now = time.time()
        with self._lock:
            timestamps = self._attempts[key]
            self._attempts[key] = [t for t in timestamps if now - t < window_seconds]
            if len(self._attempts[key]) >= max_attempts:
                return False
            self._attempts[key].append(now)
            return True

    def get_remaining(self, key: str, max_attempts: int = 5, window_seconds: int = 300) -> int:
        now = time.time()
        with self._lock:
            timestamps = [t for t in self._attempts.get(key, []) if now - t < window_seconds]
            return max(0, max_attempts - len(timestamps))


rate_limiter = MemoryRateLimiter()
