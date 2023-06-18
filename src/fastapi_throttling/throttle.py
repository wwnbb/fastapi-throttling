import ipaddress
import logging

from redis.asyncio import Redis
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)


class ThrottlingResponse(JSONResponse):
    def __init__(self):
        content = {"detail": "Too Many Requests"}
        status_code = 429
        super().__init__(status_code=status_code, content=content)


class ThrottlingMiddleware:
    """
    Middleware for throttling requests based on IP address and access token.

    The middleware uses a Redis server to keep track of the request counts.
    If a limit is reached within a specified time window, further requests
    are blocked until the window is expired.

    Attributes:
        app: The FastAPI application to apply the middleware to.
        limit: The maximum number of requests allowed within the time window.
        window: The time window in seconds.
        redis: The Redis client instance.

    Methods:
        __call__: Intercept incoming requests and apply the rate limiting.
        has_exceeded_rate_limit: Check if the number of requests has exceeded the limit
            for a given identifier.
    """

    def __init__(
        self,
        app: ASGIApp,
        limit: int = 100,
        window: int = 60,
        token_header: str = "Authorization",
        redis: Redis = Redis(),
    ) -> None:
        self.app = app
        self.token_header = token_header
        self.limit = limit
        self.window = window
        self.redis = redis
        self.key_prefix = "throttle"
        self.skip_paths: list[str] = []
        self.skip_ips: list[ipaddress.IPv4Address] = []

    async def skip_middleware(self, scope: Scope) -> bool:
        if scope["type"] != "http":
            return True

        if scope["path"] in self.skip_paths:
            return True

        client_ip = self.get_client_ip(scope)

        if client_ip in self.skip_ips:
            return True
        return False

    def get_client_ip(self, scope: Scope) -> ipaddress.IPv4Address:
        headers = Headers(scope=scope)
        client_ip = headers.get(
            "x-forwarded-for", next(iter(scope["client"][0]), None)
        )
        return ipaddress.IPv4Address(client_ip)

    def get_client_token(self, scope: Scope) -> str:
        headers = Headers(scope=scope)
        return headers.get(self.token_header)

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        try:
            client_ip = self.get_client_ip(scope)
        except Exception as e:
            logger.exception(e)
            client_ip = None

        # Throttle by IP
        if client_ip and await self.has_exceeded_rate_limit(client_ip):
            response = ThrottlingResponse()
            await response(scope, receive, send)
            return

        token = self.get_client_token(scope)
        # Throttle by Token
        if token and await self.has_exceeded_rate_limit(token):
            response = ThrottlingResponse()
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
        return

    async def has_exceeded_rate_limit(self, identifier: str) -> bool:
        key_name = f"{self.key_prefix}:{identifier}"

        current_count = await self.redis.get(key_name)
        # git ttl
        ttl = await self.redis.ttl(key_name)
        if ttl == -1:
            await self.redis.set(key_name, 1, ex=self.window)
            await self.redis.expire(key_name, self.window)
            return False

        ttl = await self.redis.ttl(key_name)
        if ttl == -1:
            logger.warning(f"Broken redis-py: ttl is -1 for {key_name}")
            await self.redis.delete(key_name)
            return False

        if current_count is None:
            # This is the first request with this identifier within the window
            await self.redis.set(
                key_name, 1, ex=self.window
            )  # Start a new window
            await self.redis.expire(key_name, self.window)
            return False

        if int(current_count) < self.limit:
            # Increase the request count
            await self.redis.incr(key_name)
            return False

        return True
