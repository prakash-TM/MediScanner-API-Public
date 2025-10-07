import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.db.database import connect_to_mongo, close_mongo_connection
from app.routes import auth, medical, imagekit
from app.utils.helpers import ResponseHelper, LoggingHelper

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    logger.info("Starting MediScanner API...")
    try:
        await connect_to_mongo()
        logger.info("MediScanner API started successfully!")
    except Exception as e:
        logger.error(f"Failed to start MediScanner API: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down MediScanner API...")
    try:
        await close_mongo_connection()
        logger.info("MediScanner API shut down successfully!")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="MediScanner API",
    description="""
    A comprehensive medical prescription management API built with FastAPI and MongoDB Atlas.
    
    ## Features
    
    * **User Management**: User registration, login, logout, and password reset
    * **Medical Records**: Upload and manage medical prescriptions with detailed medicine information
    * **Authentication**: JWT-based authentication with secure password hashing
    * **Pagination & Filtering**: Advanced querying capabilities for medical records
    * **Data Validation**: Comprehensive input validation using Pydantic models
    
    ## Authentication
    
    Most endpoints require authentication. Include your JWT token in the Authorization header:
    ```
    Authorization: Bearer <your-jwt-token>
    ```
    
    ## Data Models
    
    * **Users**: Complete user profile with contact information
    * **Medical Records**: Prescription details with patient vitals and medicine information
    * **Medicines**: Detailed medicine prescriptions with dosage and timing
    * **User Sessions**: Track user login/logout activities
    """,
    version="1.0.0",
    contact={
        "name": "MediScanner API Support",
        "email": "support@mediscanner.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions with consistent response format"""
    LoggingHelper.log_error(exc, f"HTTP Exception on {request.url}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseHelper.error_response(
            message=exc.detail,
            status_code=exc.status_code
        )
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions with consistent response format"""
    LoggingHelper.log_error(exc, f"General Exception on {request.url}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ResponseHelper.error_response(
            message="Internal server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify API status
    
    Returns the current status of the API and its dependencies
    """
    try:
        # Check database connection
        from app.db.database import db
        if db.client is None:
            raise Exception("Database not connected")
        
        # Test database connection
        await db.client.admin.command('ping')
        
        return ResponseHelper.success_response(
            data={
                "status": "healthy",
                "database": "connected",
                "version": "1.0.0"
            },
            message="API is healthy and running"
        )
    except Exception as e:
        LoggingHelper.log_error(e, "Health check")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ResponseHelper.error_response(
                message="Service unavailable",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                details={"error": str(e)}
            )
        )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information
    
    Returns basic information about the MediScanner API
    """
    return ResponseHelper.success_response(
        data={
            "name": "MediScanner API",
            "version": "1.0.0",
            "description": "Medical prescription management API",
            "docs_url": "/docs",
            "redoc_url": "/redoc"
        },
        message="Welcome to MediScanner API"
    )


# Include routers
app.include_router(auth.router)
app.include_router(medical.router)
app.include_router(imagekit.router)


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
