# MediScanner API

A comprehensive medical prescription data management API built with FastAPI and MongoDB Atlas. This API provides secure user management and medical record handling with advanced features like pagination, filtering, and JWT authentication.

## 🚀 Features

- **User Management**: Complete user registration, login and logout
- **Medical Records**: Upload and manage medical prescriptions with detailed medicine information
- **Authentication**: JWT-based authentication with secure password hashing using bcrypt
- **Pagination & Filtering**: Advanced querying capabilities for medical records
- **Data Validation**: Comprehensive input validation using Pydantic models
- **Database Optimization**: MongoDB indexes for optimized queries and performance
- **Session Tracking**: User login/logout session management
- **Comprehensive Testing**: Unit tests for all major functionality
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation

## 🛠️ Tech Stack

- **Python 3.11+**
- **FastAPI** - Modern, fast web framework for building APIs
- **MongoDB Atlas** - Cloud database service
- **PyJWT** - JWT token handling
- **Pytest** - Testing framework
- **ImageKIT** - Cloud image storage service

## 📋 Prerequisites

- Python 3.11 or higher
- MongoDB Atlas account (or local MongoDB instance)
- pip 24.0 or higher
- LLM model access
- ImageKit platform access
- JWT auth keys

## 🔧 Installation & Setup

### 1. Create Virtual Environment

```bash
python -m venv venv

# On Windows
source venv/Scripts/activate

# On macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
# Development mode
python main.py

# Or using uvicorn directly
uvicorn main:app --reload
```

The API will be available at:

- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc


## 🧪 Testing

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test Files

```bash
# Test authentication
pytest tests/test_auth.py

# Test medical records
pytest tests/test_medical.py

# Test models
pytest tests/test_models.py
```

### Test Categories

- **Unit Tests**: Test individual components and functions
- **Integration Tests**: Test API endpoints and database interactions
- **Model Tests**: Test Pydantic model validation

## 🔒 Security Features

### Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

### JWT Authentication

- Secure token generation with expiration
- Token validation and verification
- Session tracking for login/logout

### Data Validation

- Comprehensive input validation using Pydantic
- Email format validation
- Mobile number format validation
- Date format validation
- Medical data range validation

## 📊 Performance Optimizations

### Database Indexes

- Email and mobile number uniqueness indexes
- User ID indexes for medical records
- Doctor name, hospital name, and date indexes
- Medicine name indexes for filtering
- Compound indexes for complex queries

### Pagination

- Efficient pagination with skip/limit
- Configurable page sizes
- Total count and page metadata

### Query Optimization

- MongoDB aggregation pipelines for statistics
- Optimized filtering with regex patterns
- Efficient data retrieval with proper indexing

## 🚀 Deployment

### Environment Variables for Production

```env
AI_API_KEY = ai-model-api-key
AI_MODEL= ai-model-name
AI_API_BASE= ai-model-provider-base-api
MONGODB_URL= mongodb+srv://username:password@cluster.mongodb.net/
DATABASE_NAME = db-name
SECRET_KEY = jwt-auth-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES = token-expire-time-in-minutes
ALGORITHM = jwt-algorithm
PORT=8000
IMAGEKIT_PUBLIC_KEY= your-imagekit-public-key
IMAGEKIT_PRIVATE_KEY=your-imagekit-private-key
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/{your-Imagekit-id}
```


## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://choosealicense.com/licenses/mit/) file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the test files for usage examples

## 🔄 Version History

- **version-0.0.9** - Initial release with complete user management and medical records functionality
- **version-0.0.9** - Development version with core features

---

**Note**: This API is designed for medical prescription management. Ensure you comply with healthcare data regulations (HIPAA, GDPR, etc.) when handling real medical data in production environments.
