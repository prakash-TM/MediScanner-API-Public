from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ResponseHelper:
    """Helper functions for API responses"""
    
    @staticmethod
    def success_response(data: Any = None, message: str = "Success", status_code: int = 200) -> Dict[str, Any]:
        """Create a standardized success response"""
        response = {
            "success": True,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if data is not None:
            response["data"] = data
            
        return response
    
    @staticmethod
    def error_response(message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a standardized error response"""
        response = {
            "success": False,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if details:
            response["details"] = details
            
        return response


class ValidationHelper:
    """Helper functions for data validation"""
    
    @staticmethod
    def validate_object_id(object_id: str) -> bool:
        """Validate MongoDB ObjectId format"""
        try:
            from bson import ObjectId
            ObjectId(object_id)
            return True
        except Exception:
            return False
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize string input"""
        if not value:
            return ""
        return value.strip()
    
    @staticmethod
    def validate_email_format(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


class PaginationHelper:
    """Helper functions for pagination"""
    
    @staticmethod
    def calculate_pagination(page: int, limit: int, total: int) -> Dict[str, Any]:
        """Calculate pagination metadata"""
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": total_pages,
            "hasNext": has_next,
            "hasPrev": has_prev
        }
    
    @staticmethod
    def get_skip_value(page: int, limit: int) -> int:
        """Calculate skip value for MongoDB queries"""
        return (page - 1) * limit


class DateHelper:
    """Helper functions for date operations"""
    
    @staticmethod
    def format_date(date: datetime) -> str:
        """Format datetime to ISO string"""
        return date.isoformat()
    
    @staticmethod
    def parse_date(date_string: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except Exception:
            try:
                return datetime.strptime(date_string, '%Y-%m-%d')
            except Exception:
                return None
    
    @staticmethod
    def get_current_timestamp() -> datetime:
        """Get current UTC timestamp"""
        return datetime.utcnow()


class LoggingHelper:
    """Helper functions for logging"""
    
    @staticmethod
    def log_api_call(endpoint: str, method: str, user_id: Optional[str] = None, **kwargs):
        """Log API call details"""
        log_data = {
            "endpoint": endpoint,
            "method": method,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if user_id:
            log_data["user_id"] = user_id
            
        log_data.update(kwargs)
        
        logger.info(f"API Call: {log_data}")
    
    @staticmethod
    def log_error(error: Exception, context: str = "", **kwargs):
        """Log error with context"""
        log_data = {
            "error": str(error),
            "error_type": type(error).__name__,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        log_data.update(kwargs)
        
        logger.error(f"Error: {log_data}")
