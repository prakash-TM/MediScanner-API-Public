import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
import json

from main import app
from app.models import UserCreate, UserLogin
from app.utils.auth import AuthUtils


class TestUserRegistration:
    """Test user registration functionality"""
    
    @pytest.fixture
    def valid_user_data(self):
        """Valid user data for testing"""
        return {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "password": "SecurePass123!",
            "confirmPassword": "SecurePass123!",
            "age": 30,
            "mobileNumber": "1234567890",
            "photo": "https://example.com/photo.jpg"
        }
    
    @pytest.fixture
    def invalid_user_data(self):
        """Invalid user data for testing"""
        return {
            "name": "J",
            "email": "invalid-email",
            "password": "weak",
            "confirmPassword": "different",
            "age": 200,
            "mobileNumber": "123"
        }
    
    @pytest.mark.asyncio
    async def test_user_registration_success(self, valid_user_data):
        """Test successful user registration"""
        with patch('app.routes.auth.get_users_collection') as mock_collection:
            # Mock database operations
            mock_users_collection = AsyncMock()
            mock_collection.return_value = mock_users_collection
            
            # Mock user doesn't exist
            mock_users_collection.find_one.side_effect = [None, None]  # email check, mobile check
            mock_users_collection.insert_one.return_value.inserted_id = "user123"
            
            # Mock get_user_by_id
            with patch('app.routes.auth.UserQueries.get_user_by_id') as mock_get_user:
                mock_get_user.return_value = {
                    "id": "user123",
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "age": 30,
                    "mobileNumber": "1234567890",
                    "photo": "https://example.com/photo.jpg",
                    "createdAt": "2023-01-01T00:00:00",
                    "updatedAt": "2023-01-01T00:00:00"
                }
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post("/auth/register", json=valid_user_data)
                
                assert response.status_code == 201
                data = response.json()
                assert data["success"] is True
                assert data["message"] == "User created successfully"
                assert "data" in data
                assert data["data"]["name"] == "John Doe"
                assert data["data"]["email"] == "john.doe@example.com"
    
    @pytest.mark.asyncio
    async def test_user_registration_duplicate_email(self, valid_user_data):
        """Test user registration with duplicate email"""
        with patch('app.routes.auth.get_users_collection') as mock_collection:
            mock_users_collection = AsyncMock()
            mock_collection.return_value = mock_users_collection
            
            # Mock user already exists
            mock_users_collection.find_one.return_value = {"id": "existing_user"}
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/auth/register", json=valid_user_data)
            
            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False
            assert "already exists" in data["message"]
    
    @pytest.mark.asyncio
    async def test_user_registration_invalid_data(self, invalid_user_data):
        """Test user registration with invalid data"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/auth/register", json=invalid_user_data)
        
        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Test user login functionality"""
    
    @pytest.fixture
    def valid_login_data(self):
        """Valid login data for testing"""
        return {
            "email": "john.doe@example.com",
            "password": "SecurePass123!"
        }
    
    @pytest.fixture
    def user_data(self):
        """User data for testing"""
        return {
            "id": "user123",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "age": 30,
            "mobileNumber": "1234567890",
            "passwordHash": "$2b$12$example_hash",
            "createdAt": "2023-01-01T00:00:00",
            "updatedAt": "2023-01-01T00:00:00"
        }
    
    @pytest.mark.asyncio
    async def test_user_login_success(self, valid_login_data, user_data):
        """Test successful user login"""
        with patch('app.routes.auth.get_users_collection') as mock_users_collection, \
             patch('app.routes.auth.get_user_sessions_collection') as mock_sessions_collection, \
             patch('app.routes.auth.UserQueries.get_user_by_email') as mock_get_user, \
             patch('app.routes.auth.UserQueries.create_user_session') as mock_create_session, \
             patch('app.utils.auth.AuthUtils.verify_password') as mock_verify_password:
            
            # Mock user exists and password is correct
            mock_get_user.return_value = user_data
            mock_verify_password.return_value = True
            mock_create_session.return_value = "session123"
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/auth/login", json=valid_login_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Login successful"
            assert "data" in data
            assert "token" in data["data"]
            assert data["data"]["user"]["email"] == "john.doe@example.com"
    
    @pytest.mark.asyncio
    async def test_user_login_invalid_credentials(self, valid_login_data):
        """Test user login with invalid credentials"""
        with patch('app.routes.auth.get_users_collection') as mock_collection, \
             patch('app.routes.auth.UserQueries.get_user_by_email') as mock_get_user:
            
            # Mock user doesn't exist
            mock_get_user.return_value = None
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/auth/login", json=valid_login_data)
            
            assert response.status_code == 401
            data = response.json()
            assert data["success"] is False
            assert "Invalid email or password" in data["message"]


class TestPasswordReset:
    """Test password reset functionality"""
    
    @pytest.fixture
    def reset_data(self):
        """Password reset data for testing"""
        return {
            "email": "john.doe@example.com",
            "oldPassword": "OldPass123!",
            "newPassword": "NewPass123!",
            "confirmPassword": "NewPass123!"
        }
    
    @pytest.mark.asyncio
    async def test_password_reset_success(self, reset_data, user_data):
        """Test successful password reset"""
        with patch('app.routes.auth.get_users_collection') as mock_collection, \
             patch('app.routes.auth.UserQueries.get_user_by_email') as mock_get_user, \
             patch('app.routes.auth.UserQueries.update_user_password') as mock_update_password, \
             patch('app.utils.auth.AuthUtils.verify_password') as mock_verify_password:
            
            # Mock user exists and old password is correct
            mock_get_user.return_value = user_data
            mock_verify_password.return_value = True
            mock_update_password.return_value = True
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/auth/reset-password", json=reset_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Password reset successfully"
    
    @pytest.mark.asyncio
    async def test_password_reset_invalid_old_password(self, reset_data, user_data):
        """Test password reset with invalid old password"""
        with patch('app.routes.auth.get_users_collection') as mock_collection, \
             patch('app.routes.auth.UserQueries.get_user_by_email') as mock_get_user, \
             patch('app.utils.auth.AuthUtils.verify_password') as mock_verify_password:
            
            # Mock user exists but old password is incorrect
            mock_get_user.return_value = user_data
            mock_verify_password.return_value = False
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/auth/reset-password", json=reset_data)
            
            assert response.status_code == 401
            data = response.json()
            assert data["success"] is False
            assert "Invalid old password" in data["message"]


class TestAuthUtils:
    """Test authentication utility functions"""
    
    def test_password_hashing(self):
        """Test password hashing functionality"""
        password = "TestPassword123!"
        hashed = AuthUtils.get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert AuthUtils.verify_password(password, hashed) is True
        assert AuthUtils.verify_password("wrong_password", hashed) is False
    
    def test_jwt_token_creation(self):
        """Test JWT token creation and verification"""
        user_id = "user123"
        email = "test@example.com"
        
        token = AuthUtils.create_access_token({"sub": user_id, "email": email})
        
        assert token is not None
        assert len(token) > 0
        
        # Verify token
        payload = AuthUtils.verify_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["email"] == email
    
    def test_invalid_jwt_token(self):
        """Test invalid JWT token verification"""
        invalid_token = "invalid.token.here"
        payload = AuthUtils.verify_token(invalid_token)
        assert payload is None
