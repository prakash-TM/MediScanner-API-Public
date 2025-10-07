from fastapi import APIRouter, HTTPException
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
import os
from typing import Dict, Union
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/imagekit", tags=["imagekit"])

# Initialize ImageKit
imagekit = ImageKit(
    private_key=os.getenv('IMAGEKIT_PRIVATE_KEY'),
    public_key=os.getenv('IMAGEKIT_PUBLIC_KEY'),
    url_endpoint=os.getenv('IMAGEKIT_URL_ENDPOINT')
)

from typing import Union

@router.get("/auth")
async def get_imagekit_auth() -> Dict[str, Union[str, int]]:
    """
    Generate authentication parameters for client-side ImageKit upload.
    This endpoint is called by the frontend before uploading files.
    
    Returns:
        - token: str - Authentication token
        - expire: int - Expiration timestamp
        - signature: str - Request signature
    """
    try:
        auth_params = imagekit.get_authentication_parameters()
        return auth_params
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate authentication parameters: {str(e)}"
        )


# Optional: Server-side upload method (if you want to upload from backend)
@router.post("/upload")
async def upload_to_imagekit(file_data: bytes, file_name: str, folder: str = "/medical-prescriptions"):
    """
    Optional: Upload file directly from backend to ImageKit.
    This is an alternative if you want to handle uploads server-side.
    """
    try:
        upload_options = UploadFileRequestOptions(
            file=file_data,
            file_name=file_name,
            folder=folder,
            tags=["prescription", "medical"]
        )
        
        result = imagekit.upload_file(upload_options)
        
        return {
            "url": result.url,
            "file_id": result.file_id,
            "name": result.name,
            "thumbnail_url": result.thumbnail_url or result.url
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload to ImageKit: {str(e)}"
        )


