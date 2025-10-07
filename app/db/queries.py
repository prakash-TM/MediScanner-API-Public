from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from app.models import User, MedicalRecord, UserSession, MedicalRecordFilter
from app.db.database import get_database
import logging
from app.utils.helpers import LoggingHelper

logger = logging.getLogger(__name__)



class UserQueries:
    """User database queries"""
    
    @staticmethod
    async def create_user(collection: AsyncIOMotorCollection, user_data: Dict[str, Any]) -> str:
        """Create a new user and return the user ID"""
        try:
            user_data["createdAt"] = datetime.utcnow()
            user_data["updatedAt"] = datetime.utcnow()
            
            result = await collection.insert_one(user_data)
            logger.info(f"User created with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    @staticmethod
    async def get_user_by_email(collection: AsyncIOMotorCollection, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            user = await collection.find_one({"email": email})
            if user:
                user["id"] = str(user["_id"])
                del user["_id"]
            return user
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            raise
    
    @staticmethod
    async def get_user_by_id(collection: AsyncIOMotorCollection, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            user = await collection.find_one({"_id": ObjectId(user_id)})
            if user:
                user["id"] = str(user["_id"])
                del user["_id"]
            return user
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            raise
    
    @staticmethod
    async def update_user_password(collection: AsyncIOMotorCollection, user_id: str, password_hash: str) -> bool:
        """Update user password"""
        try:
            result = await collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"passwordHash": password_hash, "updatedAt": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user password: {e}")
            raise

class UserSessionQueries:
    """User session database queries"""
    
    @staticmethod
    async def create_user_session(collection: AsyncIOMotorCollection, session_data: Dict[str, Any]) -> str:
        """Create a new user session and return the session ID"""
        try:
            result = await collection.insert_one(session_data)
            logger.info(f"User session created with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating user session: {e}")
            raise
    
    @staticmethod
    async def update_session_logout(collection: AsyncIOMotorCollection, jwt_token: str) -> bool:
        """Update session with logout time"""
        try:
            result = await collection.update_one(
                {"jwtToken": jwt_token, "logoutTime": None},
                {"$set": {"logoutTime": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating session logout: {e}")
            raise
    
    @staticmethod
    async def get_active_session(collection: AsyncIOMotorCollection, jwt_token: str) -> Optional[Dict[str, Any]]:
        """Get active session by JWT token"""
        try:
            session = await collection.find_one({
                "jwtToken": jwt_token,
                "logoutTime": None
            })
            if session:
                session["id"] = str(session["_id"])
                del session["_id"]
            return session
        except Exception as e:
            logger.error(f"Error getting active session: {e}")
            raise

class PrescriptionQueries:

    @staticmethod
    async def create_prescription(prescription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new prescription"""
        try:
            db = await get_database()
            collection = db["medical_records"]

            prescription_data["createdAt"] = datetime.utcnow()
            prescription_data["updatedAt"] = datetime.utcnow()

            result = await collection.insert_one(prescription_data)
            prescription_data["_id"] = str(result.inserted_id)

            return prescription_data
        except Exception as e:
            LoggingHelper.log_error(e, "Error creating prescription", {"data": prescription_data})
            raise

    @staticmethod
    async def get_prescription_by_id(prescription_id: str) -> Optional[Dict[str, Any]]:
        """Get a single prescription by ID"""
        try:
            db = await get_database()
            collection = db["medical_records"]

            # Convert string ID to ObjectId for MongoDB query
            if not ObjectId.is_valid(prescription_id):
                return None
            
            prescription = await collection.find_one({"_id": ObjectId(prescription_id)})
            
            if prescription:
                # Convert ObjectId to string for response
                prescription["_id"] = str(prescription["_id"])
                if "userId" in prescription and isinstance(prescription["userId"], ObjectId):
                    prescription["userId"] = str(prescription["userId"])
            
            return prescription
        except Exception as e:
            LoggingHelper.log_error(e, "Error fetching prescription by ID", {"prescription_id": prescription_id})
            raise

    @staticmethod
    async def get_all_prescriptions(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all prescriptions with pagination"""
        try:
            db = await get_database()
            collection = db["medical_records"]

            cursor = collection.find().skip(skip).limit(limit).sort("createdAt", -1)
            prescriptions = await cursor.to_list(length=limit)

            # Convert ObjectId to string for all documents
            for prescription in prescriptions:
                if "_id" in prescription and isinstance(prescription["_id"], ObjectId):
                    prescription["_id"] = str(prescription["_id"])
                if "userId" in prescription and isinstance(prescription["userId"], ObjectId):
                    prescription["userId"] = str(prescription["userId"])

            return prescriptions
        except Exception as e:
            LoggingHelper.log_error(e, "Error fetching all prescriptions", {"skip": skip, "limit": limit})
            raise

    @staticmethod
    async def get_prescriptions_by_user_id(user_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all prescriptions for a specific user"""
        try:
            db = await get_database()
            collection = db["medical_records"]

            # Handle both string and ObjectId for userId
            user_id_query = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id

            cursor = collection.find({"userId": user_id_query}).skip(skip).limit(limit).sort("createdAt", -1)
            prescriptions = await cursor.to_list(length=limit)

            # Convert ObjectId to string for all documents
            for prescription in prescriptions:
                if "_id" in prescription and isinstance(prescription["_id"], ObjectId):
                    prescription["_id"] = str(prescription["_id"])
                if "userId" in prescription and isinstance(prescription["userId"], ObjectId):
                    prescription["userId"] = str(prescription["userId"])

            return prescriptions
        except Exception as e:
            LoggingHelper.log_error(e, "Error fetching prescriptions by user ID", {"user_id": user_id})
            raise

    @staticmethod
    async def update_prescription(prescription_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a prescription by ID"""
        try:
            db = await get_database()
            collection = db["medical_records"]

            # Validate ObjectId
            if not ObjectId.is_valid(prescription_id):
                return None

            update_data["updatedAt"] = datetime.utcnow()

            result = await collection.update_one(
                {"_id": ObjectId(prescription_id)},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                return await PrescriptionQueries.get_prescription_by_id(prescription_id)

            return None
        except Exception as e:
            LoggingHelper.log_error(e, "Error updating prescription", {"prescription_id": prescription_id, "update_data": update_data})
            raise

    @staticmethod
    async def delete_prescription(prescription_id: str) -> bool:
        """Delete a prescription by ID"""
        try:
            db = await get_database()
            collection = db["medical_records"]

            # Validate ObjectId
            if not ObjectId.is_valid(prescription_id):
                return False

            result = await collection.delete_one({"_id": ObjectId(prescription_id)})
            return result.deleted_count > 0
        except Exception as e:
            LoggingHelper.log_error(e, "Error deleting prescription", {"prescription_id": prescription_id})
            raise

    @staticmethod
    async def search_prescriptions(
        user_id: Optional[str] = None,
        doctor_name: Optional[str] = None,
        hospital_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search prescriptions with filters"""
        try:
            db = await get_database()
            collection = db["medical_records"]

            # Build query
            query = {}
            
            if user_id:
                query["userId"] = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            
            if doctor_name:
                query["doctorName"] = {"$regex": doctor_name, "$options": "i"}
            
            if hospital_name:
                query["hospitalName"] = {"$regex": hospital_name, "$options": "i"}
            
            if date_from or date_to:
                query["createdAt"] = {}
                if date_from:
                    query["createdAt"]["$gte"] = date_from
                if date_to:
                    query["createdAt"]["$lte"] = date_to

            cursor = collection.find(query).skip(skip).limit(limit).sort("createdAt", -1)
            prescriptions = await cursor.to_list(length=limit)

            # Convert ObjectId to string
            for prescription in prescriptions:
                if "_id" in prescription and isinstance(prescription["_id"], ObjectId):
                    prescription["_id"] = str(prescription["_id"])
                if "userId" in prescription and isinstance(prescription["userId"], ObjectId):
                    prescription["userId"] = str(prescription["userId"])

            return prescriptions
        except Exception as e:
            LoggingHelper.log_error(e, "Error searching prescriptions", {
                "user_id": user_id,
                "doctor_name": doctor_name,
                "hospital_name": hospital_name
            })
            raise

    @staticmethod
    async def get_prescription_count(user_id: Optional[str] = None) -> int:
        """Get total count of prescriptions"""
        try:
            db = await get_database()
            collection = db["medical_records"]

            query = {}
            if user_id:
                query["userId"] = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id

            count = await collection.count_documents(query)
            return count
        except Exception as e:
            LoggingHelper.log_error(e, "Error counting prescriptions", {"user_id": user_id})
            raise