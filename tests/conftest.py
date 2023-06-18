import asyncio
from typing import Annotated

import fastapi
import pytest
from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from redis.asyncio import Redis

from fastapi_throttling import ThrottlingMiddleware


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def redis_client():
    client = Redis(host="localhost", port=6379, db=9)
    yield client
    await client.close()


@pytest.fixture(scope="module")
def app(redis_client) -> fastapi.FastAPI:
    fake_secret_token = "coneofsilence"

    fake_db = {
        "foo": {
            "id": "foo",
            "title": "Foo",
            "description": "There goes my hero",
        },
        "bar": {"id": "bar", "title": "Bar", "description": "The bartenders"},
    }

    app = FastAPI()
    app.add_middleware(
        ThrottlingMiddleware, limit=5, window=1, redis=redis_client
    )

    class Item(BaseModel):
        id: str
        title: str
        description: str | None = None

    @app.get("/items/{item_id}", response_model=Item)
    async def read_main(item_id: str, x_token: Annotated[str, Header()]):
        if x_token != fake_secret_token:
            raise HTTPException(
                status_code=400, detail="Invalid X-Token header"
            )
        if item_id not in fake_db:
            raise HTTPException(status_code=404, detail="Item not found")
        return fake_db[item_id]

    @app.post("/items/", response_model=Item)
    async def create_item(item: Item, x_token: Annotated[str, Header()]):
        if x_token != fake_secret_token:
            raise HTTPException(
                status_code=400, detail="Invalid X-Token header"
            )
        if item.id in fake_db:
            raise HTTPException(status_code=400, detail="Item already exists")
        fake_db[item.id] = item
        return item

    return app


@pytest.fixture(scope="module")
def client(app) -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture()
async def flush_redis(redis_client):
    yield
    await redis_client.flushdb()
