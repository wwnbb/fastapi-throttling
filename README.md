[![Upload Python Package](https://github.com/wwnbb/fastapi-throttling/actions/workflows/publish.yml/badge.svg?branch=master)](https://github.com/wwnbb/fastapi-throttling/actions/workflows/publish.yml)

## FastAPI Throttling Middleware

FastAPI Throttling Middleware is a rate-limiting middleware for the FastAPI web framework. It uses a Redis server for request tracking and allows you to throttle incoming requests based on IP address and access token.
Features

    IP-based throttling: Limit requests based on client's IP address.
    Token-based throttling: Limit requests based on user access token.
    Redis integration: Uses Redis as a fast, in-memory data store to track request count.
    Configurable rate limits: Set your own request limit and time window.

Installation

First, ensure you have a running Redis server.

Next, install the middleware library.

```bash

pip install fastapi-throttling

```

Usage

Here's a basic example of how to use the middleware:

```python

from fastapi import FastAPI, Request, HTTPException
from fastapi_throttling import ThrottlingMiddleware

app = FastAPI()
app.add_middleware(ThrottlingMiddleware, limit=100, window=60)
```

In this example, the middleware will limit to 100 requests per 60 seconds, either by IP or by user token.


##### License

GNU LESSER GENERAL PUBLIC LICENSE Version 2.1
