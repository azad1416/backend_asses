import logging
import time
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api import customers, dashboard, orders, products
from app.core.config import get_settings
from app.core.database import get_db
from app.utils.exceptions import AppException, ErrorResponse

settings = get_settings()

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            LOGS_DIR / "app.log",
            maxBytes=10_000_000,
            backupCount=5,
        ),
    ],
)

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    alembic_ini = base_dir / "alembic.ini"
    if not alembic_ini.exists():
        logger.warning("alembic.ini not found at %s — skipping migrations", alembic_ini)
        return
    logger.info("Running database migrations...")
    alembic_cfg = Config(str(alembic_ini))
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations completed")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    run_migrations()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Production-ready Inventory & Order Management System API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info("Request: %s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            "Response: %s %s - Status: %s - Time: %.3fs",
            request.method,
            request.url.path,
            response.status_code,
            process_time,
        )
        return response
    except Exception:
        logger.exception("Unhandled error during request: %s %s", request.method, request.url.path)
        raise


@app.exception_handler(AppException)
async def app_exception_handler(_request: Request, exc: AppException):
    logger.warning("Application error: %s", exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(message=exc.message).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    errors = exc.errors()
    message = errors[0]["msg"] if errors else "Validation error"
    logger.warning("Validation error: %s", errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(message=message).model_dump(),
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(_request: Request, exc: SQLAlchemyError):
    logger.error("Database error: %s", str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(message="Database error occurred").model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(_request: Request, exc: Exception):
    logger.exception("Internal server error: %s", str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(message="Internal server error").model_dump(),
    )


app.include_router(products.router, prefix="/api")
app.include_router(customers.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "app": settings.app_name, "database": "connected"}
    except Exception as exc:
        logger.error("Health check database error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "app": settings.app_name,
                "database": "disconnected",
                "message": str(exc),
            },
        )
