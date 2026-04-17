from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
import os

from api.chat import router as chat_router
from api.search import router as search_router
from api.admin import router as admin_router
from db.database import init_db

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB and resources on startup."""
    logger.info("Starting RAG Documentation Assistant...")
    await init_db()
    logger.info("Database initialized.")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="RAG Documentation Assistant",
    description="Answers natural-language questions over your docs with citations.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration - support environment-based origins
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

# Clean up origins (remove whitespace)
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS]

logger.info("CORS allowed origins", origins=ALLOWED_ORIGINS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(chat_router,   prefix="/api", tags=["Chat"])
app.include_router(search_router, prefix="/api", tags=["Search"])
app.include_router(admin_router,  prefix="/admin", tags=["Admin"])


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "0.1.0"}
