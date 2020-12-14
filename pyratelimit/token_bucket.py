from heapq import heappop, heappush
from threading import Condition, Lock, Thread
from time import get_clock_info
from time import monotonic as _time
from typing import Final, List, Optional, Tuple

_clock_resolution = get_clock_info("monotonic").resolution


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

    def fill(self, n: int = 1) -> None:
        """Fill the bucket with n tokens."""
        with self._cond:
            self.n_token = min(self.n_token + n, self._bucket_size)
            self._cond.notify()

    def consume(self, n: int = 1, timeout: Optional[float] = None) -> bool:
        """Consume n tokens from the bucket.

        When timeout specified, it will block for at most timeout seconds.
        If consume does not complete successfully in that interval, return false.
        Return true otherwise.
        """
        rc = False
        endtime: Optional[float] = None
        with self._cond:
            while self.n_token < n:
                if timeout is not None:
                    if endtime is None:
                        endtime = _time() + timeout
                    else:
                        timeout = endtime - _time()
                        if timeout <= 0:
                            break
                self._cond.wait(timeout)
            else:
                self.n_token -= n
                rc = True
        return rc


class TokenFillerWorker:
    """A worker for filling buckets with tokens periodically"""

    def __init__(self) -> None:
        self._scheduled: List[Tuple[float, TokenBucket]] = []
        self._stopping = False
        self._thread = Thread(name="token_filler_worker", target=self._work)
        self._thread.setDaemon(True)
        self._thread.start()

    def register(self, tb: TokenBucket) -> None:
        """Register a token bucket to the worker.

        Args:
            tb (TokenBucket): A token bucket.

        Raises:
            RuntimeError: When called after stopping the worker.
        """
        if self._stopping:
            raise RuntimeError("Token filler worker already stopped.")
        heappush(self._scheduled, (_time() + 1 / tb._rate, tb))

    def _work(self) -> None:
        """Run until `stop()` is called."""
        try:
            while True:
                self._work_once()
                if self._stopping:
                    break
        finally:
            self._stopping = False

    def _work_once(self) -> None:
        """Run one iteration of the work loop"""
        end_time = _time() + _clock_resolution
        while self._scheduled:
            when, _ = self._scheduled[0]
            if when >= end_time:
                break
            when, tb = heappop(self._scheduled)
            tb.fill()
            heappush(self._scheduled, (when + 1 / tb._rate, tb))

    def stop(self) -> None:
        """Stop the worker."""
        self._stopping = True
        self._thread.join()
        self._scheduled.clear()


_token_filler_worker = TokenFillerWorker()
