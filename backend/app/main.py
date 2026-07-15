import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import SessionLocal
from app.routers import auth_router, applications_router, policy_router
from app.routers.processing import router as processing_router
from app.routers.demo import router as demo_router
from app.seed import seed_demo_users, seed_policy_rules
from app.core.logging import get_logger
from app.core.exceptions import add_exception_handlers
from app.schemas.common import HealthResponse
from datetime import datetime
import os

logger = get_logger("startup")

# Application initialization
logger.info("=" * 80)
logger.info("Loan Application Processing Agent API - Starting up")
logger.info("=" * 80)

app = FastAPI(
    title="Loan Application Processing Agent API",
    description="Backend API for AI Decisioning Agent and Underwriting Dashboard",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

logger.info("FastAPI application created")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS middleware configured")

# Add exception handlers
add_exception_handlers(app)
logger.info("Exception handlers registered")

# Seed demo users on startup if empty
logger.info("Running seed script...")
try:
    db = SessionLocal()
    try:
        seed_demo_users(db)
        seed_policy_rules(db)
        logger.info("Seed script completed successfully")
    finally:
        db.close()
except Exception as e:
    logger.error(f"Seed script failed: {str(e)}", exc_info=True)
    logger.warning("Application will continue, but initial data may not be populated")

from fastapi.staticfiles import StaticFiles
from app.routers.reports import router as reports_router
from app.routers.evaluation import router as evaluation_router

# Register routers
app.include_router(auth_router)
app.include_router(applications_router)
app.include_router(policy_router)
app.include_router(processing_router)
app.include_router(demo_router)
app.include_router(reports_router)
app.include_router(evaluation_router)
logger.info("API routers registered")

# Mount uploads directory to serve files statically
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
logger.info("Static uploads directory mounted")

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {"message": "Loan Application Processing Agent API is online."}

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    db_type = "SQLite" if "sqlite" in os.getenv("DATABASE_URL", "").lower() else "PostgreSQL"
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        database=db_type
    )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

