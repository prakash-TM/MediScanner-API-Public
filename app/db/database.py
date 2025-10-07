import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING, DESCENDING
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """Database connection and management class"""
    
    client: Optional[AsyncIOMotorClient] = None
    database = None


# Create database instance
db = Database()


async def get_database() -> AsyncIOMotorClient:
    """Get database connection"""
    return db.database


async def connect_to_mongo():
    """Create database connection"""
    try:
        # Get MongoDB connection string from environment variables
        mongo_url = os.getenv("MONGODB_URL")
        database_name = os.getenv("DATABASE_NAME")
        
        logger.info(f"Connecting to MongoDB: {mongo_url}")
        
        # Create motor client
        db.client = AsyncIOMotorClient(mongo_url)
        db.database = db.client[database_name]
        
        # Test the connection
        await db.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB!")
        
        # Create indexes for better performance
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")


async def create_indexes():
    """Create database indexes for optimized queries"""
    try:
        # Users collection indexes
        users_collection = db.database.users
        await users_collection.create_indexes([
            IndexModel([("email", ASCENDING)], unique=True),
            IndexModel([("mobileNumber", ASCENDING)], unique=True),
            IndexModel([("createdAt", DESCENDING)])
        ])
        
        # Medical records collection indexes
        medical_records_collection = db.database.medical_records
        await medical_records_collection.create_indexes([
            IndexModel([("userId", ASCENDING)]),
            IndexModel([("doctorName", ASCENDING)]),
            IndexModel([("hospitalName", ASCENDING)]),
            IndexModel([("date", ASCENDING)]),
            IndexModel([("createdAt", DESCENDING)]),
            IndexModel([("userId", ASCENDING), ("createdAt", DESCENDING)]),
            IndexModel([("medicines.name", ASCENDING)])  # For medicine name filtering
        ])
        
        # User sessions collection indexes
        user_sessions_collection = db.database.user_sessions
        await user_sessions_collection.create_indexes([
            IndexModel([("userId", ASCENDING)]),
            IndexModel([("jwtToken", ASCENDING)], unique=True),
            IndexModel([("loginTime", DESCENDING)]),
            IndexModel([("logoutTime", ASCENDING)])
        ])
        
        logger.info("Database indexes created successfully!")
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")
        raise


# Collection getters
async def get_users_collection():
    """Get users collection"""
    return db.database.users


async def get_user_sessions_collection():
    """Get user sessions collection"""
    return db.database.user_sessions
