import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
import json

from main import app
from app.models import MedicalRecordFilter, Medicine


class TestMedicalRecordCreation:
    """Test medical record creation functionality"""
    
    @pytest.fixture
    def valid_medical_record_data(self):
        """Valid medical record data for testing"""
        return {
            "serialNo": 1,
            "age": 30,
            "weight": 70.5,
            "height": 175.0,
            "temperature": 36.5,
            "hospitalName": "City General Hospital",
            "doctorName": "Dr. Smith",
            "date": "2023-12-01",
            "medicines": [
                {
                    "id": "med1",
                    "name": "Paracetamol",
                    "quantity": 10,
                    "timeOfIntake": "morning",
                    "beforeOrAfterMeals": "after"
                },
                {
                    "id": "med2",
                    "name": "Vitamin D",
                    "quantity": 5,
                    "timeOfIntake": "evening",
                    "beforeOrAfterMeals": "before"
                }
            ],
            "reportImages": ["https://example.com/report1.jpg", "https://example.com/report2.jpg"]
        }
    
    @pytest.fixture
    def invalid_medical_record_data(self):
        """Invalid medical record data for testing"""
        return {
            "serialNo": 0,  # Invalid: must be > 0
            "age": 200,     # Invalid: must be <= 150
            "weight": -10,  # Invalid: must be > 0
            "height": 500,  # Invalid: must be <= 300
            "temperature": 60,  # Invalid: must be <= 50
            "hospitalName": "A",  # Invalid: too short
            "doctorName": "B",    # Invalid: too short
            "date": "invalid-date",  # Invalid: wrong format
            "medicines": []  # Invalid: empty list
        }
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        return {
            "id": "user123",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "age": 30,
            "mobileNumber": "1234567890"
        }
    
    @pytest.mark.asyncio
    async def test_medical_record_creation_success(self, valid_medical_record_data, mock_user):
        """Test successful medical record creation"""
        with patch('app.routes.medical.get_current_user') as mock_get_user, \
             patch('app.routes.medical.get_medical_records_collection') as mock_collection, \
             patch('app.routes.medical.MedicalRecordQueries.create_medical_record') as mock_create_record, \
             patch('app.routes.medical.MedicalRecordQueries.get_medical_record_by_id') as mock_get_record:
            
            # Mock authenticated user
            mock_get_user.return_value = mock_user
            
            # Mock database operations
            mock_medical_collection = AsyncMock()
            mock_collection.return_value = mock_medical_collection
            mock_create_record.return_value = "record123"
            
            # Mock created record
            created_record = {
                "id": "record123",
                "userId": "user123",
                "serialNo": 1,
                "age": 30,
                "weight": 70.5,
                "height": 175.0,
                "temperature": 36.5,
                "hospitalName": "City General Hospital",
                "doctorName": "Dr. Smith",
                "date": "2023-12-01",
                "medicines": [
                    {
                        "id": "med1",
                        "name": "Paracetamol",
                        "quantity": 10,
                        "timeOfIntake": "morning",
                        "beforeOrAfterMeals": "after"
                    }
                ],
                "reportImages": ["https://example.com/report1.jpg"],
                "createdAt": "2023-12-01T10:00:00"
            }
            mock_get_record.return_value = created_record
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/medical/records",
                    json=valid_medical_record_data,
                    headers={"Authorization": "Bearer mock_token"}
                )
            
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Medical record created successfully"
            assert "data" in data
            assert data["data"]["id"] == "record123"
            assert data["data"]["userId"] == "user123"
    
    @pytest.mark.asyncio
    async def test_medical_record_creation_invalid_data(self, invalid_medical_record_data, mock_user):
        """Test medical record creation with invalid data"""
        with patch('app.routes.medical.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/medical/records",
                    json=invalid_medical_record_data,
                    headers={"Authorization": "Bearer mock_token"}
                )
            
            assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_medical_record_creation_unauthorized(self, valid_medical_record_data):
        """Test medical record creation without authentication"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/medical/records", json=valid_medical_record_data)
        
        assert response.status_code == 403  # Forbidden


class TestMedicalRecordRetrieval:
    """Test medical record retrieval functionality"""
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        return {
            "id": "user123",
            "name": "John Doe",
            "email": "john.doe@example.com"
        }
    
    @pytest.fixture
    def mock_medical_records(self):
        """Mock medical records data"""
        return {
            "records": [
                {
                    "id": "record1",
                    "userId": "user123",
                    "serialNo": 1,
                    "age": 30,
                    "weight": 70.5,
                    "height": 175.0,
                    "temperature": 36.5,
                    "hospitalName": "City General Hospital",
                    "doctorName": "Dr. Smith",
                    "date": "2023-12-01",
                    "medicines": [
                        {
                            "id": "med1",
                            "name": "Paracetamol",
                            "quantity": 10,
                            "timeOfIntake": "morning",
                            "beforeOrAfterMeals": "after"
                        }
                    ],
                    "createdAt": "2023-12-01T10:00:00"
                }
            ],
            "total": 1,
            "page": 1,
            "limit": 10,
            "totalPages": 1,
            "hasNext": False,
            "hasPrev": False
        }
    
    @pytest.mark.asyncio
    async def test_get_medical_records_success(self, mock_user, mock_medical_records):
        """Test successful medical records retrieval"""
        with patch('app.routes.medical.get_current_user') as mock_get_user, \
             patch('app.routes.medical.get_medical_records_collection') as mock_collection, \
             patch('app.routes.medical.MedicalRecordQueries.get_medical_records') as mock_get_records:
            
            # Mock authenticated user
            mock_get_user.return_value = mock_user
            
            # Mock database operations
            mock_medical_collection = AsyncMock()
            mock_collection.return_value = mock_medical_collection
            mock_get_records.return_value = mock_medical_records
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/medical/records",
                    headers={"Authorization": "Bearer mock_token"}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert len(data["data"]["records"]) == 1
            assert data["data"]["total"] == 1
    
    @pytest.mark.asyncio
    async def test_get_medical_records_with_filters(self, mock_user, mock_medical_records):
        """Test medical records retrieval with filters"""
        with patch('app.routes.medical.get_current_user') as mock_get_user, \
             patch('app.routes.medical.get_medical_records_collection') as mock_collection, \
             patch('app.routes.medical.MedicalRecordQueries.get_medical_records') as mock_get_records:
            
            # Mock authenticated user
            mock_get_user.return_value = mock_user
            
            # Mock database operations
            mock_medical_collection = AsyncMock()
            mock_collection.return_value = mock_medical_collection
            mock_get_records.return_value = mock_medical_records
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/medical/records?doctorName=Smith&hospitalName=City&page=1&limit=5",
                    headers={"Authorization": "Bearer mock_token"}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_get_medical_record_by_id_success(self, mock_user):
        """Test successful medical record retrieval by ID"""
        with patch('app.routes.medical.get_current_user') as mock_get_user, \
             patch('app.routes.medical.get_medical_records_collection') as mock_collection, \
             patch('app.routes.medical.MedicalRecordQueries.get_medical_record_by_id') as mock_get_record:
            
            # Mock authenticated user
            mock_get_user.return_value = mock_user
            
            # Mock database operations
            mock_medical_collection = AsyncMock()
            mock_collection.return_value = mock_medical_collection
            
            # Mock record
            record = {
                "id": "record123",
                "userId": "user123",
                "serialNo": 1,
                "age": 30,
                "weight": 70.5,
                "height": 175.0,
                "temperature": 36.5,
                "hospitalName": "City General Hospital",
                "doctorName": "Dr. Smith",
                "date": "2023-12-01",
                "medicines": [
                    {
                        "id": "med1",
                        "name": "Paracetamol",
                        "quantity": 10,
                        "timeOfIntake": "morning",
                        "beforeOrAfterMeals": "after"
                    }
                ],
                "createdAt": "2023-12-01T10:00:00"
            }
            mock_get_record.return_value = record
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/medical/records/record123",
                    headers={"Authorization": "Bearer mock_token"}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["id"] == "record123"
    
    @pytest.mark.asyncio
    async def test_get_medical_record_not_found(self, mock_user):
        """Test medical record retrieval for non-existent record"""
        with patch('app.routes.medical.get_current_user') as mock_get_user, \
             patch('app.routes.medical.get_medical_records_collection') as mock_collection, \
             patch('app.routes.medical.MedicalRecordQueries.get_medical_record_by_id') as mock_get_record:
            
            # Mock authenticated user
            mock_get_user.return_value = mock_user
            
            # Mock database operations
            mock_medical_collection = AsyncMock()
            mock_collection.return_value = mock_medical_collection
            mock_get_record.return_value = None  # Record not found
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/medical/records/nonexistent",
                    headers={"Authorization": "Bearer mock_token"}
                )
            
            assert response.status_code == 404
            data = response.json()
            assert data["success"] is False
            assert "not found" in data["message"]
    
    @pytest.mark.asyncio
    async def test_get_medical_record_unauthorized_access(self, mock_user):
        """Test medical record retrieval for record belonging to different user"""
        with patch('app.routes.medical.get_current_user') as mock_get_user, \
             patch('app.routes.medical.get_medical_records_collection') as mock_collection, \
             patch('app.routes.medical.MedicalRecordQueries.get_medical_record_by_id') as mock_get_record:
            
            # Mock authenticated user
            mock_get_user.return_value = mock_user
            
            # Mock database operations
            mock_medical_collection = AsyncMock()
            mock_collection.return_value = mock_medical_collection
            
            # Mock record belonging to different user
            record = {
                "id": "record123",
                "userId": "different_user",  # Different user ID
                "serialNo": 1,
                "age": 30,
                "weight": 70.5,
                "height": 175.0,
                "temperature": 36.5,
                "hospitalName": "City General Hospital",
                "doctorName": "Dr. Smith",
                "date": "2023-12-01",
                "medicines": [],
                "createdAt": "2023-12-01T10:00:00"
            }
            mock_get_record.return_value = record
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/medical/records/record123",
                    headers={"Authorization": "Bearer mock_token"}
                )
            
            assert response.status_code == 403
            data = response.json()
            assert data["success"] is False
            assert "Access denied" in data["message"]


class TestMedicalRecordStats:
    """Test medical record statistics functionality"""
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        return {
            "id": "user123",
            "name": "John Doe",
            "email": "john.doe@example.com"
        }
    
    @pytest.mark.asyncio
    async def test_get_medical_records_stats_success(self, mock_user):
        """Test successful medical records statistics retrieval"""
        with patch('app.routes.medical.get_current_user') as mock_get_user, \
             patch('app.routes.medical.get_medical_records_collection') as mock_collection:
            
            # Mock authenticated user
            mock_get_user.return_value = mock_user
            
            # Mock database operations
            mock_medical_collection = AsyncMock()
            mock_collection.return_value = mock_medical_collection
            
            # Mock aggregation result
            mock_medical_collection.aggregate.return_value.to_list.return_value = [{
                "totalRecords": 5,
                "uniqueDoctors": 3,
                "uniqueHospitals": 2,
                "totalMedicines": 15,
                "dateRange": {
                    "earliest": "2023-01-01",
                    "latest": "2023-12-01"
                }
            }]
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/medical/records/stats",
                    headers={"Authorization": "Bearer mock_token"}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["totalRecords"] == 5
            assert data["data"]["uniqueDoctors"] == 3
            assert data["data"]["uniqueHospitals"] == 2
            assert data["data"]["totalMedicines"] == 15
