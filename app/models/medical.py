from pydantic import BaseModel, Field, validator, HttpUrl, field_serializer, ConfigDict
from typing import List, Optional, Any
from bson import ObjectId
from datetime import datetime
from .user import Medicine


class MedicalRecordBase(BaseModel):
    """Base medical record model"""
    serialNo: int = Field(..., gt=0, description="Serial number must be greater than 0")
    age: int = Field(..., ge=1, le=150, description="Patient age between 1 and 150")
    weight: float = Field(..., gt=0, le=500, description="Weight in kg, must be between 0 and 500")
    height: float = Field(..., gt=0, le=300, description="Height in cm, must be between 0 and 300")
    temperature: float = Field(..., ge=90, le=115, description="Temperature in Fahrenheit, must be between 90 and 115")
    hospitalName: str = Field(..., min_length=2, max_length=200, description="Hospital name")
    doctorName: str = Field(..., min_length=2, max_length=200, description="Doctor name")
    date: str = Field(..., description="Date of prescription in YYYY-MM-DD format")
    medicines: List[Medicine] = Field(..., min_items=1, description="List of prescribed medicines")
    reportImages: Optional[List[str]] = Field(None, description="Optional list of report image URLs or base64 strings")

    @validator('date')
    def validate_date(cls, v):
        """Validate date format"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')

    @validator('medicines')
    def validate_medicines(cls, v):
        """Validate medicines list"""
        if not v:
            raise ValueError('At least one medicine must be provided')
        return v


class MedicalRecord(MedicalRecordBase):
    """Medical record model for database storage"""
    id: str
    userId: str
    createdAt: datetime

    class Config:
        from_attributes = True


class MedicalRecordFilter(BaseModel):
    """Medical record filter model for querying"""
    doctorName: Optional[str] = None
    hospitalName: Optional[str] = None
    date: Optional[str] = None
    medicineName: Optional[str] = None
    page: int = Field(1, ge=1, description="Page number, must be >= 1")
    limit: int = Field(10, ge=1, le=100, description="Items per page, must be between 1 and 100")

    @validator('date')
    def validate_date(cls, v):
        """Validate date format if provided"""
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError('Date must be in YYYY-MM-DD format')
        return v

class Medicine(BaseModel):
    id: str = Field(default="")
    name: Optional[str] = None
    quantity: Optional[int] = None
    timeOfIntake: Optional[str] = None
    beforeOrAfterMeals: Optional[str] = None

class PrescriptionData(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    userId: Optional[str] = None
    serialNo: Optional[int] = None
    patientName: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    temperature: Optional[float] = None
    hospitalName: Optional[str] = None
    doctorName: Optional[str] = None
    date: Optional[str] = None
    medicines: List[Medicine] = Field(default_factory=list)
    reportImages: List[str] = Field(default_factory=list)
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    @field_serializer('id')
    def serialize_id(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()}
    )

class PrescriptionResponse(BaseModel):
    success: bool
    message: str
    count: int
    data: List[PrescriptionData]

class FileDetail(BaseModel):
    url: HttpUrl
    fileId: str
    name: str

class PrescriptionUploadRequest(BaseModel):
    prescriptionUrls: List[HttpUrl]
    fileDetails: List[FileDetail]