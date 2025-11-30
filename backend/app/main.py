"""Main FastAPI application."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, UploadFile, File, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from .config import settings
from .ingestion.models import IngestionRequest, IngestionResponse
from .ingestion.service import IngestionService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global ingestion service
ingestion_service: IngestionService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifecycle manager for FastAPI app."""
    global ingestion_service

    # Startup
    logger.info("Starting application...")
    ingestion_service = IngestionService()
    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    if ingestion_service:
        await ingestion_service.close()
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Enterprise-grade RAG system with multi-tenancy for public sector",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}


# Readiness check endpoint
@app.get("/ready")
async def readiness_check() -> dict[str, str]:
    """Readiness check endpoint."""
    if not ingestion_service:
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"status": "ready", "version": settings.app_version}


# Ingestion endpoints
@app.post("/api/v1/ingest", response_model=IngestionResponse)
async def ingest_document(
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_tenant_id),
) -> IngestionResponse:
    """Ingest a document for a tenant."""
    if not ingestion_service:
        raise HTTPException(status_code=503, detail="Ingestion service not available")

    try:
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


@app.delete("/api/v1/documents/{document_id}")
async def delete_document(
    document_id: str,
    tenant_id: str = Depends(get_tenant_id),
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


@app.get("/api/v1/collection/stats")
async def get_collection_stats(
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, any]:
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


# Root endpoint
@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "PubSec Info Assistant API",
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
