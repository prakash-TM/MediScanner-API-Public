from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re


class Medicine(BaseModel):
    """Medicine model for embedded documents in medical records"""
    id: str
    name: str
    quantity: int = Field(..., gt=0, description="Quantity must be greater than 0")
    timeOfIntake: str = Field(..., description="Time of intake: morning, afternoon, evening, night, or custom")
    beforeOrAfterMeals: str = Field(..., description="Before or after meals: before, after, or custom")


class UserBase(BaseModel):
    """Base user model with common fields"""
    name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    age: int = Field(..., ge=1, le=150, description="User's age between 1 and 150")
    mobileNumber: str = Field(..., description="User's mobile number")
    photo: Optional[str] = Field(None, description="Optional user photo URL or base64 string")

    @validator('mobileNumber')
    def validate_mobile_number(cls, v):
        """Validate mobile number format"""
        # Remove any non-digit characters
        digits_only = re.sub(r'\D', '', v)
        if len(digits_only) < 10 or len(digits_only) > 15:
            raise ValueError('Mobile number must be between 10 and 15 digits')
        return v


class UserCreate(UserBase):
    """User creation model with password validation"""
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    confirmPassword: str = Field(..., description="Password confirmation")

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

    @validator('confirmPassword')
    def passwords_match(cls, v, values):
        """Validate that password and confirmPassword match"""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str

class User(UserBase):
    """User model for database storage and responses"""
    id: str
    passwordHash: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User response model (excludes password)"""
    id: str
    name: str
    email: str
    age: int
    mobileNumber: str
    photo: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class UserSession(BaseModel):
    """User session model for tracking login/logout"""
    id: str
    userId: str
    loginTime: datetime
    logoutTime: Optional[datetime] = None
    jwtToken: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response model"""
    user: UserResponse
    token: str
    message: str = "Login successful"
