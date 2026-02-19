import time
import asyncio
from collections import defaultdict, deque
from fastapi import Header, HTTPException, status, Request

from app.config import settings

_rate_store = defaultdict(deque)
_rate_lock = asyncio.Lock()


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """
    Optional API key. If API_KEY is set in .env, enforce it.
    """
    if not settings.API_KEY:
        return
    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )


async def rate_limit(request: Request) -> None:
    """
    Simple in-memory rate limiter (per client IP).
    """
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = float(settings.RATE_LIMIT_WINDOW_SECONDS)
    limit = int(settings.RATE_LIMIT_REQUESTS)

    async with _rate_lock:
        q = _rate_store[ip]
        while q and (now - q[0]) > window:
            q.popleft()

        if len(q) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {limit}/{int(window)}s",
            )

        q.append(now)