# pyratelimit

_pyratelimit_ is a rate limit implemantation in Python.

## Installation

## Usage

```python
from concurrent import futures
from datetime import datetime
from typing import Optional

import requests

from pyratelimit import Per, RateLimit


class ApiClient:
    def __init__(self, limit: RateLimit) -> None:
        self._limit = limit

    def call(self, url: str) -> Optional[int]:
        if self._limit.wait():
            response = requests.get(url)
            return response.status_code
        return None


api_client = ApiClient(RateLimit(Per(1, 1), 1))

with futures.ThreadPoolExecutor(max_workers=3) as executor:
    fs = [
        executor.submit(
            api_client.call,
            url,
        )
        for url in [
            "http://example.com/",
            "http://example.com/",
            "http://example.com/",
            "http://example.com/",
            "http://example.com/"
        ]
    ]
    for f in futures.as_completed(fs):
        print(datetime.now(), f.result())
```

## License
