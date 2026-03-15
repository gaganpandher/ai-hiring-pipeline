from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Starting {settings.APP_NAME} [{settings.APP_ENV}]")

    try:
        from app.core.database import check_db_connection, init_db
        if await check_db_connection():
            await init_db()
    except Exception as e:
        logger.warning(f"Database startup warning: {e}")

    try:
        from app.core.redis import init_redis
        await init_redis()
    except Exception as e:
        logger.warning(f"Redis startup warning: {e}")

    try:
        from app.core.kafka import check_kafka_connection, create_topics
        if await check_kafka_connection():
            await create_topics()
    except Exception as e:
        logger.warning(f"Kafka startup warning: {e}")

    logger.info("✅ App ready")
    yield

    try:
        from app.core.kafka import close_producer
        from app.core.redis import close_redis
        await close_producer()
        await close_redis()
    except Exception as e:
        logger.warning(f"Shutdown warning: {e}")
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} is running 🚀", "version": "1.0.0"}


@app.get("/api/v1/health")
async def health():
    results = {"mysql": "unchecked", "redis": "unchecked", "kafka": "unchecked"}
    try:
        from app.core.database import check_db_connection
        results["mysql"] = "up" if await check_db_connection() else "down"
    except Exception:
        results["mysql"] = "down"
    try:
        from app.core.redis import get_redis
        await (await get_redis()).ping()
        results["redis"] = "up"
    except Exception:
        results["redis"] = "down"
    try:
        from app.core.kafka import check_kafka_connection
        results["kafka"] = "up" if await check_kafka_connection() else "down"
    except Exception:
        results["kafka"] = "down"
    all_ok = all(v == "up" for v in results.values())
    return {"status": "healthy" if all_ok else "degraded", "services": results}


# ── Routers added safely as we build each feature ─────────
for module, prefix, tag in [
    ("app.api.auth",         "/api/v1/auth",         "auth"),
    ("app.api.jobs",         "/api/v1/jobs",         "jobs"),
    ("app.api.applications", "/api/v1/applications", "applications"),
    ("app.api.analytics",    "/api/v1/analytics",    "analytics"),
]:
    try:
        import importlib
        mod = importlib.import_module(module)
        app.include_router(mod.router, prefix=prefix, tags=[tag])
    except Exception:
        pass