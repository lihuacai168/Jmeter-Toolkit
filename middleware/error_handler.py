"""Error handling middleware."""

import traceback
from typing import Callable

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from loguru import logger

from models.responses import APIResponse


async def error_handler_middleware(request: Request, call_next: Callable) -> Response:
    """Global error handling middleware."""
    try:
        response = await call_next(request)
        return response
    except HTTPException as exc:
        logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content=APIResponse.error_response(message=exc.detail, code=f"HTTP_{exc.status_code}").dict(),
        )
    except Exception as exc:
        logger.error(f"Unhandled exception: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content=APIResponse.error_response(message="Internal server error", code="INTERNAL_SERVER_ERROR").dict(),
        )


class SecurityMiddleware:
    """Security headers middleware."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":

            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    # Add security headers
                    headers.update(
                        {
                            b"x-content-type-options": b"nosniff",
                            b"x-frame-options": b"DENY",
                            b"x-xss-protection": b"1; mode=block",
                            b"strict-transport-security": b"max-age=31536000; includeSubDomains",
                            b"referrer-policy": b"strict-origin-when-cross-origin",
                        }
                    )
                    message["headers"] = list(headers.items())
                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)
