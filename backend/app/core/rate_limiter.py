"""Rate Limiter for ReconX Elite.

Implements per-scan rate limiting with:
- Default 5 req/sec (stealth mode)
- Max 50 req/sec (aggressive mode)
- Per-scan rate limiting via Redis
"""

from __future__ import annotations

import logging
from enum import Enum

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class ScanMode(Enum):
    """Scan aggressiveness modes."""

    STEALTH = "stealth"  # 5 req/sec
    BALANCED = "balanced"  # 20 req/sec
    AGGRESSIVE = "aggressive"  # 50 req/sec


MODE_RATES: dict[ScanMode, int] = {
    ScanMode.STEALTH: 5,
    ScanMode.BALANCED: 20,
    ScanMode.AGGRESSIVE: 50,
}

# Redis key prefixes
RATE_LIMIT_KEY_PREFIX = "reconx:rate_limit"
RATE_LIMIT_WINDOW = 1  # 1 second window


class RateLimiter:
    """Per-scan rate limiter using Redis token bucket."""

    def __init__(self, redis_client: redis.Redis | None = None):
        self.redis = redis_client

    def _get_key(self, scan_id: str, resource: str) -> str:
        """Generate rate limit key for scan and resource."""
        return f"{RATE_LIMIT_KEY_PREFIX}:{scan_id}:{resource}"

    async def check_rate_limit(
        self, scan_id: str, resource: str = "default", mode: ScanMode = ScanMode.BALANCED
    ) -> tuple[bool, int]:
        """Check if request is within rate limit.

        Args:
            scan_id: The scan identifier
            resource: Resource being rate limited (e.g., 'http', 'dns')
            mode: Scan mode determining max rate

        Returns:
            Tuple of (allowed, remaining_requests)
        """
        if not self.redis:
            # No Redis, allow all
            return True, MODE_RATES[mode]

        key = self._get_key(scan_id, resource)
        max_requests = MODE_RATES[mode]

        try:
            pipe = self.redis.pipeline()

            # Get current count
            pipe.get(key)
            # Increment count
            pipe.incr(key)
            # Set expiry if not exists
            pipe.expire(key, RATE_LIMIT_WINDOW)

            results = await pipe.execute()
            current_count = int(results[0] or 0)

            # Check if allowed
            allowed = current_count < max_requests
            remaining = max(0, max_requests - current_count - 1)

            if not allowed:
                logger.warning(
                    "Rate limit exceeded for scan %s resource %s: %s/%s",
                    scan_id,
                    resource,
                    current_count,
                    max_requests,
                )

            return allowed, remaining

        except Exception as e:
            logger.error("Rate limit check failed: %s", e)
            # Fail open - allow request
            return True, max_requests

    async def get_current_rate(self, scan_id: str, resource: str = "default") -> int:
        """Get current request rate for scan.

        Args:
            scan_id: The scan identifier
            resource: Resource being checked

        Returns:
            Current requests in the window
        """
        if not self.redis:
            return 0

        key = self._get_key(scan_id, resource)
        try:
            value = await self.redis.get(key)
            return int(value or 0)
        except Exception as e:
            logger.error("Failed to get current rate: %s", e)
            return 0

    async def reset_rate_limit(self, scan_id: str, resource: str = "default") -> None:
        """Reset rate limit for a scan resource.

        Args:
            scan_id: The scan identifier
            resource: Resource to reset
        """
        if not self.redis:
            return

        key = self._get_key(scan_id, resource)
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error("Failed to reset rate limit: %s", e)


class ScanRateLimiter:
    """High-level scan rate limiter for tools."""

    def __init__(self, redis_client: redis.Redis | None = None):
        self.limiter = RateLimiter(redis_client)

    async def check_http_request(self, scan_id: str, mode: ScanMode = ScanMode.BALANCED) -> bool:
        """Check if HTTP request is allowed.

        Args:
            scan_id: The scan identifier
            mode: Scan mode

        Returns:
            True if allowed
        """
        allowed, _ = await self.limiter.check_rate_limit(scan_id, "http", mode)
        return allowed

    async def check_dns_query(self, scan_id: str, mode: ScanMode = ScanMode.BALANCED) -> bool:
        """Check if DNS query is allowed.

        Args:
            scan_id: The scan identifier
            mode: Scan mode

        Returns:
            True if allowed
        """
        allowed, _ = await self.limiter.check_rate_limit(scan_id, "dns", mode)
        return allowed

    async def check_port_scan(self, scan_id: str, port_count: int = 1, mode: ScanMode = ScanMode.BALANCED) -> bool:
        """Check if port scan batch is allowed.

        Args:
            scan_id: The scan identifier
            port_count: Number of ports to scan
            mode: Scan mode

        Returns:
            True if allowed
        """
        # Port scans are more expensive, check against larger limit
        max_rate = MODE_RATES[mode]
        if port_count > max_rate:
            logger.warning(
                "Port count %s exceeds rate limit %s for scan %s",
                port_count,
                max_rate,
                scan_id,
            )
            return False

        allowed, _ = await self.limiter.check_rate_limit(scan_id, "port_scan", mode)
        return allowed

    def get_delay_for_mode(self, mode: ScanMode) -> float:
        """Get recommended delay between requests for mode.

        Args:
            mode: Scan mode

        Returns:
            Delay in seconds
        """
        rates = {
            ScanMode.STEALTH: 0.2,  # 5 req/sec = 0.2s between
            ScanMode.BALANCED: 0.05,  # 20 req/sec = 0.05s between
            ScanMode.AGGRESSIVE: 0.02,  # 50 req/sec = 0.02s between
        }
        return rates.get(mode, 0.05)


# Global instances
_rate_limiter: RateLimiter | None = None
_scan_rate_limiter: ScanRateLimiter | None = None


def get_rate_limiter(redis_client: redis.Redis | None = None) -> RateLimiter:
    """Get or create global RateLimiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(redis_client)
    return _rate_limiter


def get_scan_rate_limiter(redis_client: redis.Redis | None = None) -> ScanRateLimiter:
    """Get or create global ScanRateLimiter instance."""
    global _scan_rate_limiter
    if _scan_rate_limiter is None:
        _scan_rate_limiter = ScanRateLimiter(redis_client)
    return _scan_rate_limiter
