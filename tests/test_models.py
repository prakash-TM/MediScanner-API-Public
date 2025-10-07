import pytest
from pydantic import ValidationError
from datetime import datetime

from app.models import (
    UserCreate, UserLogin, UserResponse, Medicine,
    MedicalRecordFilter
)


class TestUserModels:
    """Test user-related Pydantic models"""
    
    def test_user_create_valid_data(self):
        """Test UserCreate model with valid data"""
        valid_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "password": "SecurePass123!",
            "confirmPassword": "SecurePass123!",
            "age": 30,
            "mobileNumber": "1234567890",
            "photo": "https://example.com/photo.jpg"
        }
        
        user = UserCreate(**valid_data)
        assert user.name == "John Doe"
        assert user.email == "john.doe@example.com"
        assert user.password == "SecurePass123!"
        assert user.confirmPassword == "SecurePass123!"
        assert user.age == 30
        assert user.mobileNumber == "1234567890"
        assert user.photo == "https://example.com/photo.jpg"
    
    def test_user_create_invalid_email(self):
        """Test UserCreate model with invalid email"""
        invalid_data = {
            "name": "John Doe",
            "email": "invalid-email",
            "password": "SecurePass123!",
            "confirmPassword": "SecurePass123!",
            "age": 30,
            "mobileNumber": "1234567890"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**invalid_data)
    
    def test_user_create_weak_password(self):
        """Test UserCreate model with weak password"""
        invalid_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "password": "weak",
            "confirmPassword": "weak",
            "age": 30,
            "mobileNumber": "1234567890"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**invalid_data)
    
    def test_user_create_password_mismatch(self):
        """Test UserCreate model with password mismatch"""
        invalid_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "password": "SecurePass123!",
            "confirmPassword": "DifferentPass123!",
            "age": 30,
            "mobileNumber": "1234567890"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**invalid_data)
    
    def test_user_create_invalid_age(self):
        """Test UserCreate model with invalid age"""
        invalid_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "password": "SecurePass123!",
            "confirmPassword": "SecurePass123!",
            "age": 200,  # Invalid: too high
            "mobileNumber": "1234567890"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**invalid_data)
    
    def test_user_create_invalid_mobile(self):
        """Test UserCreate model with invalid mobile number"""
        invalid_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "password": "SecurePass123!",
            "confirmPassword": "SecurePass123!",
            "age": 30,
            "mobileNumber": "123"  # Invalid: too short
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**invalid_data)
    
    def test_user_login_valid_data(self):
        """Test UserLogin model with valid data"""
        valid_data = {
            "email": "john.doe@example.com",
            "password": "SecurePass123!"
        }
        
        login = UserLogin(**valid_data)
        assert login.email == "john.doe@example.com"
        assert login.password == "SecurePass123!"

class TestMedicineModel:
    """Test Medicine Pydantic model"""
    
    def test_medicine_valid_data(self):
        """Test Medicine model with valid data"""
        valid_data = {
            "id": "med1",
            "name": "Paracetamol",
            "quantity": 10,
            "timeOfIntake": "morning",
            "beforeOrAfterMeals": "after"
        }
        
        medicine = Medicine(**valid_data)
        assert medicine.id == "med1"
        assert medicine.name == "Paracetamol"
        assert medicine.quantity == 10
        assert medicine.timeOfIntake == "morning"
        assert medicine.beforeOrAfterMeals == "after"
    
    def test_medicine_invalid_quantity(self):
        """Test Medicine model with invalid quantity"""
        invalid_data = {
            "id": "med1",
            "name": "Paracetamol",
            "quantity": 0,  # Invalid: must be > 0
            "timeOfIntake": "morning",
            "beforeOrAfterMeals": "after"
        }
        
        with pytest.raises(ValidationError):
            Medicine(**invalid_data)
    
    def test_medicine_negative_quantity(self):
        """Test Medicine model with negative quantity"""
        invalid_data = {
            "id": "med1",
            "name": "Paracetamol",
            "quantity": -5,  # Invalid: must be > 0
            "timeOfIntake": "morning",
            "beforeOrAfterMeals": "after"
        }
        
        with pytest.raises(ValidationError):
            Medicine(**invalid_data)


class TestMedicalRecordModels:
    """Test medical record-related Pydantic models"""
    
    def test_medical_record_filter_valid_data(self):
        """Test MedicalRecordFilter model with valid data"""
        valid_data = {
            "doctorName": "Dr. Smith",
            "hospitalName": "City General",
            "date": "2023-12-01",
            "medicineName": "Paracetamol",
            "page": 1,
            "limit": 10
        }
        
        filter_obj = MedicalRecordFilter(**valid_data)
        assert filter_obj.doctorName == "Dr. Smith"
        assert filter_obj.hospitalName == "City General"
        assert filter_obj.date == "2023-12-01"
        assert filter_obj.medicineName == "Paracetamol"
        assert filter_obj.page == 1
        assert filter_obj.limit == 10
    
    def test_medical_record_filter_default_values(self):
        """Test MedicalRecordFilter model with default values"""
        filter_obj = MedicalRecordFilter()
        assert filter_obj.doctorName is None
        assert filter_obj.hospitalName is None
        assert filter_obj.date is None
        assert filter_obj.medicineName is None
        assert filter_obj.page == 1
        assert filter_obj.limit == 10
    
    def test_medical_record_filter_invalid_page(self):
        """Test MedicalRecordFilter model with invalid page number"""
        invalid_data = {
            "page": 0  # Invalid: must be >= 1
        }
        
        with pytest.raises(ValidationError):
            MedicalRecordFilter(**invalid_data)
    
    def test_medical_record_filter_invalid_limit(self):
        """Test MedicalRecordFilter model with invalid limit"""
        invalid_data = {
            "limit": 200  # Invalid: must be <= 100
        }
        
        with pytest.raises(ValidationError):
            MedicalRecordFilter(**invalid_data)
    
    def test_medical_record_filter_invalid_date(self):
        """Test MedicalRecordFilter model with invalid date format"""
        invalid_data = {
            "date": "invalid-date"  # Invalid: wrong format
        }
        
        with pytest.raises(ValidationError):
            MedicalRecordFilter(**invalid_data)
