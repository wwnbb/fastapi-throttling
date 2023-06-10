from fastapi import HTTPException, Request, Response
from redis import Redis
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.types import ASGIApp


class ThrottlingError(HTTPException):
    def __init__(self):
        super().__init__(status_code=429, detail="Too Many Requests")


class ThrottlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for throttling requests based on IP address and access token.

    The middleware uses a Redis server to keep track of the request counts.
    If a limit is reached within a specified time window, further requests
    are blocked until the window is expired.

    Attributes:
        app: The FastAPI application to apply the middleware to.
        limit: The maximum number of requests allowed within the time window.
        window: The time window in seconds.
        redis: The Redis server instance.

    Methods:
        __call__: Intercept incoming requests and apply the rate limiting.
        is_rate_limited: Check if the number of requests has exceeded the limit for
            a given identifier.
    """

    def __init__(
        self,
        app: ASGIApp,
        limit: int = 100,
        window: int = 60,
        redis_host: str | None = 'localhost',
        redis_port: int | None = 6379,
        redis: Redis | None = None,
    ):
        self.app = app
        self.limit = limit
        self.window = window

        if redis:
            self.redis = redis
        elif redis_host and redis_port:
            self.redis = Redis(host=redis_host, port=redis_port)
        else:
            raise ValueError('Redis server not configured')

        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        client_ip = request.client.host
        token = request.headers.get('Authorization')

        # Throttle by IP
        if self.has_exceeded_rate_limit(client_ip):
            raise ThrottlingError

        # Throttle by Token
        if token and self.has_exceeded_rate_limit(token):
            raise ThrottlingError

        response = await call_next(request)
        return response

    def has_exceeded_rate_limit(self, identifier: str) -> bool:
        current_count = self.redis.get(identifier)

        if current_count is None:
            # This is the first request with this identifier within the window
            self.redis.set(identifier, 1, ex=self.window)  # Start a new window
            return False

        if int(current_count) < self.limit:
            # Increase the request count
            self.redis.incr(identifier)
            return False

        return True
