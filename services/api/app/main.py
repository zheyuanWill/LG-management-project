"""
LG Management API - Main Application
"""
import logging
import sys
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(name)s %(levelname)s %(message)s", force=True)
logging.getLogger("kingdee").setLevel(logging.DEBUG)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.config import settings
from app.core.exceptions import BusinessError
from app.routers import health, auth, customer, order, product, contract, procurement, inventory, tracking, settlement, file, user, notification, workflow, dashboard, integration, ai_agent, analytics, iso_process, ship_repair

app = FastAPI(
    title="LG Management API",
    description="修船项目管理 & 供应链系统 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS — In DEBUG mode, allow all origins for local development convenience.
# In production, only CORS_ORIGINS from settings are allowed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(auth.router, prefix="/api")
app.include_router(customer.router, prefix="/api")
app.include_router(order.router, prefix="/api")
app.include_router(order.quote_router, prefix="/api")
app.include_router(product.router, prefix="/api")
app.include_router(product.supplier_router, prefix="/api")
app.include_router(product.category_router, prefix="/api")
app.include_router(contract.router, prefix="/api")
app.include_router(procurement.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(tracking.router, prefix="/api")
app.include_router(settlement.router, prefix="/api")
app.include_router(file.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(notification.router, prefix="/api")
app.include_router(workflow.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(integration.router, prefix="/api")
app.include_router(ai_agent.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(iso_process.router, prefix="/api/iso", tags=["ISO Process"])
app.include_router(ship_repair.router, prefix="/api")

# Ensure upload directory exists
UPLOAD_DIR = "/app/uploads/ship-repair"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Serve static files for uploads
app.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")


# ---------------------------------------------------------------------------
# Global Exception Handlers
# ---------------------------------------------------------------------------

logger = logging.getLogger("lg-management")


@app.exception_handler(BusinessError)
async def business_error_handler(request, exc: BusinessError):
    """Handle custom business exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


@app.exception_handler(PydanticValidationError)
async def pydantic_validation_handler(request, exc: PydanticValidationError):
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "请求参数验证失败",
            "detail": str(exc),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Catch-all handler for unhandled exceptions."""
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误，请稍后重试",
            "detail": str(exc) if settings.DEBUG else None,
        },
    )


# ---------------------------------------------------------------------------
# Optional: Slow Query Simulation Middleware
# Enable with: SLOW_QUERY_ENABLED=true
# ---------------------------------------------------------------------------
import os
if os.environ.get("SLOW_QUERY_ENABLED", "").lower() in ("true", "1"):
    from app.core.middleware import SlowQueryMiddleware
    app.add_middleware(SlowQueryMiddleware)
    logger.warning("⚠️  SlowQueryMiddleware is ENABLED — API responses will be artificially delayed!")


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("LG Management API starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("LG Management API shutting down...")
