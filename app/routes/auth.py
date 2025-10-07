from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any
import logging

from app.models import UserCreate, UserLogin, UserResponse, LoginResponse
from app.db.database import get_users_collection, get_user_sessions_collection
from app.db.queries import UserQueries, UserSessionQueries
from app.utils.auth import AuthUtils, get_current_user, security, create_token_for_user
from app.utils.helpers import ResponseHelper, LoggingHelper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate):
    """
    Create a new user account
    
    - **name**: User's full name (2-100 characters)
    - **email**: Valid email address
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit, special char)
    - **confirmPassword**: Must match password
    - **age**: User's age (1-150)
    - **mobileNumber**: Mobile number (10-15 digits)
    - **photo**: Optional user photo URL or base64 string
    """
    try:
        LoggingHelper.log_api_call("/auth/register", "POST")
        
        # Get users collection
        users_collection = await get_users_collection()
        
        # Check if user already exists
        existing_user = await UserQueries.get_user_by_email(users_collection, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Check if mobile number already exists
        existing_mobile = await users_collection.find_one({"mobileNumber": user_data.mobileNumber})
        if existing_mobile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this mobile number already exists"
            )
        
        # Hash password
        password_hash = AuthUtils.get_password_hash(user_data.password)
        
        # Prepare user data for database
        user_dict = user_data.dict(exclude={"password", "confirmPassword"})
        user_dict["passwordHash"] = password_hash
        
        # Create user
        user_id = await UserQueries.create_user(users_collection, user_dict)
        
        # Get created user (without password)
        created_user = await UserQueries.get_user_by_id(users_collection, user_id)
        user_response = UserResponse(**created_user)
        
        LoggingHelper.log_api_call("/auth/register", "POST", user_id=user_id, success=True)
        
        return ResponseHelper.success_response(
            data=user_response.dict(),
            message="User created successfully",
            status_code=status.HTTP_201_CREATED
        )
        
    except HTTPException:
        raise
    except Exception as e:
        LoggingHelper.log_error(e, "User registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during user creation"
        )


@router.post("/login", response_model=Dict[str, Any])
async def login_user(login_data: UserLogin):
    """
    Login user and return JWT token
    
    - **email**: User's email address
    - **password**: User's password
    """
    try:
        LoggingHelper.log_api_call("/auth/login", "POST")
        
        # Get users collection
        users_collection = await get_users_collection()
        user_sessions_collection = await get_user_sessions_collection()
        
        # Get user by email
        user = await UserQueries.get_user_by_email(users_collection, login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not AuthUtils.verify_password(login_data.password, user["passwordHash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create JWT token
        token = create_token_for_user(user["id"], user["email"])
        
        # Create user session
        session_data = {
            "userId": user["id"],
            "loginTime": AuthUtils.get_current_timestamp(),
            "jwtToken": token
        }
        await UserSessionQueries.create_user_session(user_sessions_collection, session_data)
        
        # Prepare response
        user_response = UserResponse(**user)
        login_response = LoginResponse(
            user=user_response,
            token=token,
            message="Login successful"
        )
        
        LoggingHelper.log_api_call("/auth/login", "POST", user_id=user["id"], success=True)
        
        return ResponseHelper.success_response(
            data=login_response.dict(),
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        LoggingHelper.log_error(e, "User login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )


@router.post("/logout", response_model=Dict[str, Any])
async def logout_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout user and invalidate JWT token
    
    Requires valid JWT token in Authorization header
    """
    try:
        LoggingHelper.log_api_call("/auth/logout", "POST")
        
        # Get current user
        current_user = await get_current_user(credentials)
        
        # Get user sessions collection
        user_sessions_collection = await get_user_sessions_collection()
        
        # Update session with logout time
        token = credentials.credentials
        session_updated = await UserSessionQueries.update_session_logout(user_sessions_collection, token)
        
        if not session_updated:
            logger.warning(f"Session not found or already logged out for user: {current_user['id']}")
        
        LoggingHelper.log_api_call("/auth/logout", "POST", user_id=current_user["id"], success=True)
        
        return ResponseHelper.success_response(
            message="Logout successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        LoggingHelper.log_error(e, "User logout")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )
