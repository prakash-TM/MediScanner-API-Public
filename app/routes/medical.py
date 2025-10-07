from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List
import logging
import httpx
from app.models.medical import PrescriptionResponse, PrescriptionData, PrescriptionUploadRequest
from app.db.queries import PrescriptionQueries
from app.utils.auth import get_current_user
from app.utils.image_processor import PrescriptionImageProcessor


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/medicine", tags=["Medical Records"])
# router = APIRouter(prefix="/api/medical", tags=["Medical"])

@router.post("/uploadMedicalPrescription", response_model=PrescriptionResponse)
async def extract_prescription_data(
    request: PrescriptionUploadRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    if not request.prescriptionUrls or len(request.prescriptionUrls) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No prescription URLs provided. Please upload at least one image."
        )

    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

    # Validate file extensions from URLs
    for file_detail in request.fileDetails:
        file_extension = '.' + file_detail.name.lower().split('.')[-1]
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type for {file_detail.name}. Allowed types: jpg, jpeg, png, gif, webp"
            )

    try:
        processor = PrescriptionImageProcessor()

        # Download images from URLs
        image_data = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for file_detail in request.fileDetails:
                try:
                    response = await client.get(str(file_detail.url))
                    response.raise_for_status()
                    image_bytes = response.content
                    image_data.append((image_bytes, file_detail.name))
                except httpx.HTTPError as e:
                    logger.error(f"Error downloading image from {file_detail.url}: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to download image from URL: {file_detail.url}"
                    )

        print(f"@tm image_data: {len(image_data)} images downloaded")
        
        # Process images (synchronous call)
        prescriptions = processor.process_multiple_images(image_data)

        # Save prescriptions to database and associate with ImageKit details
        saved_prescriptions = []
        for i, prescription in enumerate(prescriptions):
            prescription_dict = prescription.model_dump()
            
            # Add ImageKit metadata to the prescription
            prescription_dict['imagekit_url'] = str(request.fileDetails[i].url)
            prescription_dict['imagekit_file_id'] = request.fileDetails[i].fileId
            prescription_dict['original_filename'] = request.fileDetails[i].name
            prescription_dict['user_id'] = current_user.get('id') or current_user.get('_id')
            
            saved = await PrescriptionQueries.create_prescription(prescription_dict)
            saved_prescriptions.append(PrescriptionData(**saved))
        print(f"@tm prescriptions{prescriptions}")
        return PrescriptionResponse(
            success=True,
            message=f"Successfully processed {len(prescriptions)} prescription image(s)",
            count=len(saved_prescriptions),
            data=saved_prescriptions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in extract_prescription_data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing images: {str(e)}"
        )

@router.get("/usersMedicalData", response_model=dict)
async def get_all_prescriptions(
    skip: int = 0, 
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all prescriptions for the authenticated user"""
    try:
        prescriptions = await PrescriptionQueries.get_all_prescriptions(skip=skip, limit=limit)
        return {
            "success": True,
            "count": len(prescriptions),
            "data": prescriptions
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching prescriptions: {str(e)}"
        )
