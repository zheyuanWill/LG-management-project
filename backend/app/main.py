import os
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from sqlalchemy import text

from app.config import settings
from app.db import engine, init_db
from app.models import User
from app.security import hash_password

logger.remove()
logger.add(
    sink=lambda msg: print(msg, end=""),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO",
    colorize=False,
)

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)


async def seed_admin_user() -> None:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select

    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        existing = result.scalar_one_or_none()
        if existing:
            logger.info("Admin user already exists, skipping seed.")
            return

        admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            display_name="系统管理员",
            role="admin",
        )
        session.add(admin)
        await session.commit()
        logger.warning("=" * 60)
        logger.warning("  默认管理员已创建: admin / admin123")
        logger.warning("  请尽快修改密码!")
        logger.warning("=" * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up: initializing database...")
    try:
        await init_db()
        await seed_admin_user()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.error(traceback.format_exc())

    yield

    logger.info("Shutting down: closing database connections...")
    await engine.dispose()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="LG Management API",
    description="船舶管理系统后端 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "message": str(exc)},
    )


@app.get("/health")
async def health_check():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "disconnected"},
        )


@app.get("/api/v1/health")
async def api_health_check():
    return {"status": "ok", "version": "1.0.0"}


app.mount("/temp", StaticFiles(directory=str(TEMP_DIR)), name="temp")

try:
    from app.routers import auth, users, projects, tasks, reports, risks, brokerage, spare_parts, quick_saves, knowledge, customers, files

    app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["用户"])
    app.include_router(projects.router, prefix="/api/v1/projects", tags=["项目"])
    app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["任务"])
    app.include_router(reports.router, prefix="/api/v1/reports", tags=["报告"])
    app.include_router(risks.router, prefix="/api/v1/risks", tags=["风险"])
    app.include_router(brokerage.router, prefix="/api/v1/brokerage", tags=["经纪"])
    app.include_router(spare_parts.router, prefix="/api/v1/spare-parts", tags=["备件"])
    app.include_router(quick_saves.router, prefix="/api/v1/quick-saves", tags=["随手存"])
    app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["知识库"])
    app.include_router(customers.router, prefix="/api/v1/customers", tags=["客户"])
    app.include_router(files.router, prefix="/api/v1/files", tags=["文件"])
except ImportError:
    logger.warning("Some routers not found. Creating placeholder routers...")

    from fastapi import APIRouter

    router = APIRouter()
    app.include_router(router, prefix="/api/v1")