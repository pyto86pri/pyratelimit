from pyratelimit import Per
from pyratelimit.aio.token_bucket import TokenBucket


class RateLimit:
    """A rate limit."""

    def __init__(self, per: Per, burst: int) -> None:
        self._token_bucket = TokenBucket(per.calls / per.period, burst)

    async def wait(self, n: int = 1) -> None:
        await self._token_bucket.consume(n)
