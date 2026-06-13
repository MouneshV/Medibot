"""
MediBot FastAPI Application — Main entry point.
"""

import logging
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import HealthResponse
from routers import auth_router, chat, collections

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def check_qdrant_status():
    """Check if Qdrant is accessible and has data."""
    try:
        from qdrant_client import QdrantClient
        from config import QDRANT_URL, QDRANT_COLLECTION
        
        client = QdrantClient(url=QDRANT_URL)
        
        # Check if collection exists
        if client.collection_exists(QDRANT_COLLECTION):
            # Get collection info
            collection_info = client.get_collection(QDRANT_COLLECTION)
            points_count = collection_info.points_count
            logger.info(f"✅ Qdrant Collection '{QDRANT_COLLECTION}' found with {points_count} points")
            
            if points_count == 0:
                logger.warning("⚠️  Qdrant collection is EMPTY. Run: python ingestion/ingest_fallback_only.py")
                return False, "Collection exists but is empty"
            return True, f"{points_count} points found"
        else:
            logger.warning(f"⚠️  Qdrant collection '{QDRANT_COLLECTION}' NOT FOUND")
            logger.warning("    Run: python ingestion/ingest_fallback_only.py")
            return False, "Collection not found"
    except Exception as e:
        logger.warning(f"⚠️  Cannot connect to Qdrant: {e}")
        logger.warning("    Using in-memory Qdrant (data will be lost on restart)")
        return None, str(e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    logger.info("=" * 70)
    logger.info("🏥 MediBot Backend Starting...")
    logger.info("=" * 70)
    
    # Check environment
    logger.info("\n[STARTUP CHECKS]")
    from config import GROQ_API_KEY, QDRANT_URL, QDRANT_COLLECTION
    
    if not GROQ_API_KEY or GROQ_API_KEY == "your_key_here":
        logger.error("❌ GROQ_API_KEY not set in .env file!")
    else:
        logger.info("✅ GROQ_API_KEY configured")
    
    logger.info(f"✅ Qdrant URL: {QDRANT_URL}")
    logger.info(f"✅ Collection: {QDRANT_COLLECTION}")
    
    # Check Qdrant
    logger.info("\n[QDRANT STATUS]")
    qdrant_ok, message = check_qdrant_status()
    
    if qdrant_ok is False:
        logger.warning(f"⚠️  {message}")
    elif qdrant_ok is None:
        logger.warning(f"⚠️  {message}")
    else:
        logger.info(f"✅ {message}")
    
    logger.info("\n[API ENDPOINTS]")
    logger.info("  POST   /login                 — Get JWT token")
    logger.info("  POST   /chat                  — Ask a question (requires token)")
    logger.info("  GET    /collections/{role}   — List accessible collections")
    logger.info("  GET    /health               — Health check")
    logger.info("  GET    /docs                 — Swagger UI")
    logger.info("=" * 70)
    
    yield
    
    logger.info("=" * 70)
    logger.info("🏥 MediBot Backend Shutdown")
    logger.info("=" * 70)


# Create FastAPI app
app = FastAPI(
    title="MediBot API",
    description="Advanced RAG with RBAC for MediAssist Health Network",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware (allow localhost for frontend development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router)
app.include_router(chat.router)
app.include_router(collections.router)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok", service="MediBot")


@app.get("/")
async def root():
    """Root endpoint — returns API info."""
    return {
        "service": "MediBot",
        "version": "1.0.0",
        "description": "Advanced RAG with RBAC for MediAssist Health Network",
        "status": "running",
        "docs_url": "/docs",
        "endpoints": {
            "login": "POST /login (username, password)",
            "chat": "POST /chat (requires auth token, question: str)",
            "collections": "GET /collections/{role} (requires auth token)",
            "health": "GET /health",
        },
        "demo_accounts": {
            "doctor": "dr.mehta / doctor123",
            "nurse": "nurse.priya / nurse123",
            "billing_executive": "billing.ravi / billing123",
            "technician": "tech.anand / tech123",
            "admin": "admin.sys / admin123",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
