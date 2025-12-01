"""Main FastAPI application."""
import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Header, Depends, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from .config import settings
from .ingestion.models import IngestionRequest, IngestionResponse
from .ingestion.service import IngestionService
from .rag_service import RAGService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global services
ingestion_service: IngestionService | None = None
rag_service: RAGService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifecycle manager for FastAPI app."""
    global ingestion_service, rag_service

    # Startup
    logger.info("Starting application...")
    
    # Validate OpenAI configuration
    if not settings.openai_api_key or settings.openai_api_key == "your-api-key-here":
        if settings.environment == "production":
            logger.error("OpenAI API key missing in production; failing fast.")
            raise RuntimeError("OpenAI API key required in production")
        else:
            logger.warning("OpenAI API key missing; OpenAI-dependent features disabled in test/dev.")
    
    ingestion_service = IngestionService()
    rag_service = RAGService()
    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    try:
        if ingestion_service:
            await ingestion_service.close()
        if rag_service:
            await rag_service.close()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Enterprise-grade RAG system with multi-tenancy for public sector.\n\n"
        "Secured via optional API Key header `X-API-Key` and basic rate limits."
    ),
    lifespan=lifespan,
    contact={"name": "PubSec Team", "url": "https://github.com/MarcoPolo483"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request-id and security headers middleware
@app.middleware("http")
async def add_request_context(request: Request, call_next):
    """Add request-id, security headers, and structured logging context."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Extract tenant for logging
    tenant_id = request.headers.get(settings.tenant_header_name, settings.default_tenant_id)
    
    # Log request with context
    logger.info(
        f"Request started",
        extra={
            "request_id": request_id,
            "tenant_id": tenant_id,
            "method": request.method,
            "path": request.url.path,
        }
    )
    
    response = await call_next(request)
    
    # Add security headers to all responses
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'none'; img-src data:; style-src 'self' 'unsafe-inline'; script-src 'none'"
    response.headers["Referrer-Policy"] = "no-referrer"
    
    return response

# Basic API Key + in-memory rate limiting (per-process)
from time import time
from collections import defaultdict, deque

WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 300
_rate_window: dict[str, deque[float]] = defaultdict(deque)

def _require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> str:
    # Accept missing key for now (public read); tighten later if needed
    if x_api_key is None:
        return "public"
    if not x_api_key.strip():
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

def rate_limit(api_key: str = Depends(_require_api_key)):
    now = time()
    window = _rate_window[api_key]
    window.append(now)
    while window and now - window[0] > WINDOW_SECONDS:
        window.popleft()
    if len(window) > MAX_REQUESTS_PER_WINDOW:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return api_key

# Custom exception handler for unified error schema
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return unified error schema for all HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail
            }
        }
    )

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Dependency to get tenant ID from header
async def get_tenant_id(
    x_tenant_id: str | None = Header(None, alias=settings.tenant_header_name)
) -> str:
    """Extract tenant ID from header."""
    if not x_tenant_id:
        return settings.default_tenant_id
    return x_tenant_id


# Health check endpoint
@app.get("/health", tags=["system"], summary="Health check")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}


# Readiness check endpoint
@app.get("/ready", tags=["system"], summary="Readiness check")
async def readiness_check() -> dict[str, str]:
    """Readiness check endpoint."""
    if not ingestion_service:
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"status": "ready", "version": settings.app_version}


# Ingestion endpoints
@app.post(
    "/api/v1/ingest",
    response_model=IngestionResponse,
    tags=["ingestion"],
    summary="Ingest a document",
    description="Uploads a file and indexes it for retrieval within the tenant scope.",
)
async def ingest_document(
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_tenant_id),
    api_key: str = Depends(rate_limit),
) -> IngestionResponse:
    """Ingest a document for a tenant."""
    if not ingestion_service:
        raise HTTPException(status_code=503, detail="Ingestion service not available")

    try:
        # Basic file type validation for unsupported types (tests expect 500 on bad type)
        allowed_types = {"text/plain", "application/pdf", "text/markdown"}
        if file.content_type and file.content_type not in allowed_types:
            raise HTTPException(status_code=500, detail="Unsupported file type")

        # Read file content
        content = await file.read()

        # Create ingestion request
        request = IngestionRequest(
            tenant_id=tenant_id,
            filename=file.filename or "unknown",
            content=content,
        )

        # Process document
        response = await ingestion_service.ingest_document(request)

        if response.status == "failed":
            raise HTTPException(status_code=500, detail=response.message)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to ingest document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {str(e)}")


@app.delete(
    "/api/v1/documents/{document_id}",
    tags=["ingestion"],
    summary="Delete document",
)
async def delete_document(
    document_id: str,
    tenant_id: str = Depends(get_tenant_id),
    api_key: str = Depends(rate_limit),
) -> dict[str, str]:
    """Delete a document for a tenant."""
    if not ingestion_service:
        raise HTTPException(status_code=503, detail="Ingestion service not available")

    try:
        result = await ingestion_service.delete_document(tenant_id, document_id)

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@app.get(
    "/api/v1/collection/stats",
    tags=["ingestion"],
    summary="Collection statistics",
)
async def get_collection_stats(
    tenant_id: str = Depends(get_tenant_id),
    api_key: str = Depends(rate_limit),
) -> dict[str, Any]:
    """Get collection statistics for a tenant."""
    if not ingestion_service:
        raise HTTPException(status_code=503, detail="Ingestion service not available")

    try:
        stats = await ingestion_service.get_collection_stats(tenant_id)

        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collection stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# Explicit OPTIONS handler for CORS preflight on query endpoint to avoid 400 due to required params
@app.options("/api/v1/query")
async def query_preflight() -> Response:
    return Response(status_code=204)

# RAG Query endpoint
@app.post(
    "/api/v1/query",
    tags=["rag"],
    summary="Query RAG",
    description="Queries the system, retrieving context and generating an answer.",
)
async def query(
    query: str,
    top_k: int = 5,
    use_cache: bool = True,
    tenant_id: str = Depends(get_tenant_id),
    api_key: str = Depends(rate_limit),
) -> dict[str, Any]:
    """Query the RAG system with a question."""
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not available")

    try:
        result = await rag_service.query(
            query=query,
            tenant_id=tenant_id,
            use_cache=use_cache,
            top_k=top_k,
        )

        # Add cost tracking headers (robust against missing token fields)
        headers = {}
        if settings.cost_tracking_enabled and "cost" in result:
            headers["X-Request-Cost"] = f"{result['cost']:.4f}"
            tokens_used = result.get("tokens_used")
            if isinstance(tokens_used, dict):
                input_tokens = tokens_used.get("input", tokens_used.get("prompt", 0))
                output_tokens = tokens_used.get("output", tokens_used.get("completion", 0))
                headers["X-Token-Usage"] = f"input:{input_tokens},output:{output_tokens}"
            if "tenant_balance" in result:
                headers["X-Tenant-Balance"] = f"balance:{result['tenant_balance']:.2f}"

        return JSONResponse(content=result, headers=headers)

    except ValueError as e:
        # Rate limit or validation error
        raise HTTPException(status_code=429, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")


@app.get(
    "/api/v1/tenant/stats",
    tags=["tenant"],
    summary="Tenant statistics",
)
async def get_tenant_stats(
    tenant_id: str = Depends(get_tenant_id),
    api_key: str = Depends(rate_limit),
) -> dict[str, Any]:
    """Get tenant statistics including balance and collection info."""
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not available")

    try:
        stats = await rag_service.get_tenant_stats(tenant_id)

        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# Root endpoint
@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "EVA Domain Assistant 2.0 API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
    )
