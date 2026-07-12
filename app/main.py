"""FastAPI Online Book Store Main Application Entrypoint."""

import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool
from app.api.router import api_router
from app.api.web import router as web_router
from app.core.config import settings
from app.ai.embeddings import EmbeddingService
from app.ai.vector_db import VectorDatabase

# Max seconds to wait for RAG warmup (embedding model load + vector DB init)
# before giving up and starting the server anyway. Without this, a hung
# Hugging Face Hub network check (e.g. flaky/offline internet, even when
# the model is already cached locally) can block server startup forever
# with zero error output -- the process just sits at "Waiting for
# application startup." indefinitely.
RAG_WARMUP_TIMEOUT_SECONDS = 30


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    def _warm_rag_dependencies() -> None:
        embedding_service = EmbeddingService()
        embedding_service.embed_text("warmup")
        vector_db = VectorDatabase()
        vector_db.initialize_db()

    try:
        await asyncio.wait_for(
            run_in_threadpool(_warm_rag_dependencies),
            timeout=RAG_WARMUP_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        print(
            f"RAG warmup timed out after {RAG_WARMUP_TIMEOUT_SECONDS}s (non-fatal) -- "
            "starting server anyway. This usually means a network call (e.g. Hugging "
            "Face Hub checking for model updates) is hanging. Try setting "
            "HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1 if the model is already "
            "cached locally, or check your internet connection."
        )
    except Exception as e:
        print(f"RAG warmup failed (non-fatal): {e}")

    yield
    # Shutdown tasks

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Mount Static Files directory
static_dir = "app/static" if os.path.exists("app/static") else "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates for Exception Handlers
template_dir = "app/templates" if os.path.exists("app/templates") else "templates"
templates = Jinja2Templates(directory=template_dir)

# CORS Configuration
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include Public Web Views Router
app.include_router(web_router)

# Include API V1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health Check"])
async def health_check():
    """Health check endpoint to verify API operation."""
    return {"status": "healthy", "project": settings.PROJECT_NAME}


# ── Exception Handlers ────────────────────────────────────────────────────────
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    """Custom 404 HTML Exception Handler."""
    if request.url.path.startswith("/api/"):
        return HTMLResponse(content='{"detail": "Not Found"}', status_code=404)
    return templates.TemplateResponse("404.html", {"request": request}, status_code=status.HTTP_404_NOT_FOUND)


@app.exception_handler(500)
async def custom_500_handler(request: Request, exc):
    """Custom 500 HTML Exception Handler."""
    if request.url.path.startswith("/api/"):
        return HTMLResponse(content='{"detail": "Internal Server Error"}', status_code=500)
    return templates.TemplateResponse("500.html", {"request": request}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)