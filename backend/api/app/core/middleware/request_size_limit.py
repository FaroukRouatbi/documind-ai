from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

MAX_REQUEST_SIZE = 1_000_000


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            return JSONResponse(status_code=413, content={"detail": "Request body too large"})

        body = b""
        async for chunk in request.stream():
            body += chunk
            if len(body) > MAX_REQUEST_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request body too large"},
                )

        request._body = body

        return await call_next(request)
