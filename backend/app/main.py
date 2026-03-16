from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import traceback

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Starting {settings.APP_NAME} [{settings.APP_ENV}]")

    # ── Database ──────────────────────────────────────────────
    try:
        from app.core.database import check_db_connection, init_db
        db_ok = await check_db_connection()
        if db_ok:
            await init_db()
            logger.info("✅ MySQL ready — tables created/verified")
        else:
            logger.warning("⚠️  MySQL unavailable — DB features disabled")
    except Exception as e:
        logger.warning(f"Database startup warning: {e}")

    # ── Redis ─────────────────────────────────────────────────
    try:
        from app.core.redis import init_redis
        await init_redis()
        logger.info("✅ Redis ready")
    except Exception as e:
        logger.warning(f"Redis startup warning: {e}")

    # ── Kafka ─────────────────────────────────────────────────
    try:
        from app.core.kafka import check_kafka_connection, create_topics
        kafka_ok = await check_kafka_connection()
        if kafka_ok:
            await create_topics()
            logger.info("✅ Kafka ready — topics created/verified")
        else:
            logger.warning("⚠️  Kafka unavailable — streaming disabled")
    except Exception as e:
        logger.warning(f"Kafka startup warning: {e}")

    logger.info("✅ App ready — http://localhost:8000/api/docs")
    yield

    # ── Shutdown ──────────────────────────────────────────────
    logger.info("Shutting down...")
    try:
        from app.core.kafka import close_producer
        await close_producer()
    except Exception:
        pass
    try:
        from app.core.redis import close_redis
        await close_redis()
    except Exception:
        pass
    logger.info("👋 Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI-powered hiring pipeline with real-time bias detection",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# ── Global error handler — shows real error in DEBUG mode ─────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = traceback.format_exc()
    logger.error(f"Unhandled exception on {request.url}:\n{error_detail}")
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "error": type(exc).__name__,
                "detail": str(exc),
                "traceback": error_detail.splitlines()[-8:],
            }
        )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers — imported AFTER app is created ───────────────────
# All heavy imports (SQLAlchemy, schemas, services) happen here,
# AFTER FastAPI is already constructed. This means if an import
# fails, FastAPI catches it cleanly instead of crashing at startup.
from app.api import auth, jobs, applications, analytics #, health  # noqa

#app.include_router(health.router,       prefix="/api/v1",              tags=["health"])
app.include_router(auth.router,         prefix="/api/v1/auth",         tags=["auth"])
app.include_router(jobs.router,         prefix="/api/v1/jobs",         tags=["jobs"])
app.include_router(applications.router, prefix="/api/v1/applications", tags=["applications"])
app.include_router(analytics.router,    prefix="/api/v1/analytics",    tags=["analytics"])


@app.get("/", tags=["root"])
async def root():
    return {
        "app":     settings.APP_NAME,
        "version": "1.0.0",
        "docs":    "http://localhost:8000/api/docs",
        "health":  "http://localhost:8000/api/v1/health",
    }