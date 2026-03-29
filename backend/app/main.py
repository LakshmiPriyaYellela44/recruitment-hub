from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from app.core.config import settings
from app.core.database import init_db
from app.middleware.middleware import RequestLoggingMiddleware, ExceptionHandlingMiddleware
from app.modules.auth.router import router as auth_router
from app.modules.auth.admin_router import router as auth_admin_router
from app.modules.candidate.router import router as candidate_router
from app.modules.recruiter.router import router as recruiter_router
from app.modules.recruiter.admin_router import router as recruiter_admin_router
from app.modules.recruiter.websocket_router import router as recruiter_ws_router
from app.modules.resume.router import router as resume_router
from app.modules.subscription.router import router as subscription_router
from app.modules.email.template_router import router as template_router
from app.events.config import EventConfig
from app.workers.resume_worker import start_resume_worker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable for background worker task
worker_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    from app.core.database import init_db, close_db

    global worker_task

    # Startup
    logger.info("Starting Recruitment Platform...")
    try:
        await init_db()
        logger.info("✓ Database initialized and ready")
    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {e}")
        raise

    # Initialize event infrastructure
    try:
        EventConfig.initialize()
        logger.info("✓ Event infrastructure initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize event infrastructure: {e}")
        raise

    # Start background worker for resume processing
    try:
        sqs_client = EventConfig.get_sqs_client()
        worker_task = asyncio.create_task(start_resume_worker(sqs_client))
        logger.info("✓ Resume worker started (listening on resume-processing-queue)")
    except Exception as e:
        logger.error(f"✗ Failed to start resume worker: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Recruitment Platform...")

    # Stop the worker task
    if worker_task and not worker_task.done():
        try:
            worker_task.cancel()
            await asyncio.sleep(1)  # Give worker time to shut down gracefully
            logger.info("✓ Resume worker stopped")
        except Exception as e:
            logger.error(f"✗ Error stopping resume worker: {e}")

    try:
        await close_db()
        logger.info("✓ Recruitment Platform shutdown complete")
    except Exception as e:
        logger.error(f"✗ Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ExceptionHandlingMiddleware)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/api")
app.include_router(auth_admin_router, prefix="/api")
app.include_router(candidate_router, prefix="/api")
app.include_router(recruiter_router, prefix="/api")
app.include_router(recruiter_admin_router, prefix="/api")
app.include_router(recruiter_ws_router, prefix="/api")
app.include_router(resume_router, prefix="/api")
app.include_router(subscription_router, prefix="/api")
app.include_router(template_router, prefix="/api")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.APP_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
 
