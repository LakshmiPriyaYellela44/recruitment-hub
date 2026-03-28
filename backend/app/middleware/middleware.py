import logging
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.exceptions import BaseAppException

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        logger.info(f"[{request_id}] {request.method} {request.url.path}")
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling exceptions."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except BaseAppException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_dict()
            )
        except Exception as exc:
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred",
                        "details": {}
                    }
                }
            )
