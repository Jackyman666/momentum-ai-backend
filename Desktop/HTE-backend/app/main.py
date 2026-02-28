from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import planner_router
from app.database import engine
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    print("Starting up HTE Backend...")
    print(f"Database connection: {settings.database_url.split('@')[-1]}")  # Log without password
    
    # Test database connection
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda _: None)  # Simple connection test
        print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
    
    yield
    
    # Shutdown
    print("Shutting down HTE Backend...")
    await engine.dispose()
    print("✓ Database connections closed")


app = FastAPI(
    title="HTE Backend API",
    description="Backend API for HTE project with AI-powered goal planning",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(planner_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to HTE Backend API"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

