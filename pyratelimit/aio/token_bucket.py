from asyncio import Condition, Lock, sleep
from asyncio.tasks import Task, create_task
from typing import Callable, Coroutine, Final, List, Tuple


def _create_periodic_task(
    f: Callable[[], Coroutine[object, object, None]], period: float
) -> Task[None]:
    async def wrapper() -> None:
        while True:
            await sleep(period)
            await f()

    return create_task(wrapper())


class TokenBucket:
    """A token bucket."""

    def __init__(self, rate: float, bucket_size: int) -> None:
        """Constructor for TokenBucket.

        Args:
            rate (float): The number of tokens added to the bucket per second.
                          A token is added to the bucket every 1/rate seconds.
            bucket_size (int): The maximum number of tokens the bucket can hold.

        Raises:
            ValueError: When rate or bucket_size less than or equal to 0.
        """
        if rate <= 0:
            raise ValueError("rate must be > 0")
        if bucket_size <= 0:
            raise ValueError("bucket size must be > 0")
        self._rate: Final[float] = rate
        self._bucket_size: Final[int] = bucket_size
        self.n_token = bucket_size
        self._cond = Condition(Lock())
        _token_filler_worker.register(self)

    async def fill(self, n: int = 1) -> None:
        """Fill the bucket with n tokens."""
        async with self._cond:
            self.n_token = min(self.n_token + n, self._bucket_size)
            self._cond.notify()

    async def consume(self, n: int = 1) -> None:
        """Consume n tokens from the bucket."""
        async with self._cond:
            while self.n_token < n:
                await self._cond.wait()
            else:
                self.n_token -= n


class TokenFillerWorker:
    """A worker for filling buckets with tokens periodically"""

    def __init__(self) -> None:
        self._scheduled: List[Tuple[float, TokenBucket]] = []
        self._stopping = False
        self._tasks: List[Task[None]] = []

    def register(self, tb: TokenBucket) -> None:
        """Register a token bucket to the worker.

        Args:
            tb (TokenBucket): A token bucket.

        Raises:
            RuntimeError: When called after stopping the worker.
        """
        if self._stopping:
            raise RuntimeError("Token filler worker already stopped.")
        self._tasks.append(_create_periodic_task(tb.fill, 1 / tb._rate))

    def stop(self) -> None:
        """Stop the worker."""
        self._stopping = True
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()


_token_filler_worker = TokenFillerWorker()
