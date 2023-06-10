import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redis import Redis

from fastapi_throttling.throttle import ThrottlingError, ThrottlingMiddleware


def test_ThrottlingMiddleware(app: FastAPI, redisdb: Redis):
    """
    Test if app can handle 100 requests per second
    """

    app.add_middleware(ThrottlingMiddleware, limit=2, window=1, redis=redisdb)
    client = TestClient(app)
    client.host = '192.168.0.1'

    with pytest.raises(ThrottlingError):
        for _ in range(3):
            client.get("/")

    time.sleep(1)
    for _ in range(2):
        client.get("/")
