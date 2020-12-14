from dataclasses import dataclass
from typing import Optional

from pyratelimit.token_bucket import TokenBucket


@dataclass
class Per:
    calls: int
    period: int


class RateLimit:
    """A rate limit."""

    def __init__(self, per: Per, burst: int) -> None:
        self._token_bucket = TokenBucket(per.calls / per.period, burst)

    def wait(self, n: int = 1, timeout: Optional[float] = None) -> bool:
        return self._token_bucket.consume(n, timeout)
