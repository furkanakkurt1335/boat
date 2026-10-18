"""Simple in-memory rate limiter for auth endpoints.

Uses a sliding window counter per IP address. No external dependencies —
Cloudflare WAF handles the heavy lifting; this is a basic protection layer.
"""

import threading
import time
from collections import defaultdict

from fastapi import HTTPException, Request, status


class RateLimiter:
    """Thread-safe sliding window rate limiter backed by an in-memory dict."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # {ip: [(timestamp, ...), ...]}
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._check_count = 0

    def check(self, ip: str, limit: int, window: int) -> bool:
        """Return True if the request is allowed, False if rate-limited."""
        now = time.monotonic()

        with self._lock:
            self._check_count += 1
            if self._check_count % 100 == 0:
                self._cleanup(window)

            # Drop timestamps outside the current window
            cutoff = now - window
            self._requests[ip] = [ts for ts in self._requests[ip] if ts > cutoff]

            if len(self._requests[ip]) >= limit:
                return False

            self._requests[ip].append(now)
            return True

    def reset(self) -> None:
        """Clear all tracked requests. Useful for testing."""
        with self._lock:
            self._requests.clear()
            self._check_count = 0

    def _cleanup(self, window: int) -> None:
        """Remove entries older than 2*window. Called with lock held."""
        cutoff = time.monotonic() - 2 * window
        stale_keys = [
            ip
            for ip, timestamps in self._requests.items()
            if not timestamps or timestamps[-1] < cutoff
        ]
        for key in stale_keys:
            del self._requests[key]


# Module-level singleton
_limiter = RateLimiter()


def create_rate_limit(limit: int = 10, window: int = 60):
    """Factory that returns a FastAPI dependency with the given limits.

    Args:
        limit: Maximum number of requests allowed within the window.
        window: Time window in seconds.
    """

    async def rate_limit_dep(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        if not _limiter.check(ip, limit=limit, window=window):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
            )

    return rate_limit_dep
