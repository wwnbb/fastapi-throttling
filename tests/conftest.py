import asyncio
import random
import string
from typing import Annotated

import fastapi
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI, Header, HTTPException
from httpx import AsyncClient
from pydantic import BaseModel
from redis.asyncio import Redis

from fastapi_throttling import ThrottlingMiddleware

@pytest.fixture(scope="session")
def event_loop():
    """Overrides pytest default function scoped event loop"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def redis_client():
    r = Redis(host="localhost", port=6379, db=9)
    yield r
    await r.close()


@pytest.fixture(scope="session")
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
        ThrottlingMiddleware, limit=5, window=5, redis=redis_client
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


@pytest.fixture(scope='session')
async def client(app):
    """Async http client for FastAPI application, ASGI init signals handled by
    LifespanManager.
    """
    async with LifespanManager(app, startup_timeout=100, shutdown_timeout=100):
        base_chars = ''.join(random.choices(string.ascii_uppercase, k=4))
        async with AsyncClient(app=app, base_url=f"http://{base_chars}") as ac:
            yield ac


@pytest.fixture()
async def flush_redis(redis_client):
    yield
    await redis_client.flushdb()
