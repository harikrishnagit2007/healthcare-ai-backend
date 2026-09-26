import os
from pathlib import Path
from typing import Optional

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Form,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Healthcare AI Backend",
    description="Beyond Prediction - Healthcare AI Backend",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# UPLOAD DIRECTORY
# ============================================================

UPLOAD_DIR = Path("uploads")

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# REQUEST MODELS
# ============================================================

class HealthcareRequest(BaseModel):
    question: str
    symptom_text: Optional[str] = ""


class NearbyCareRequest(BaseModel):
    latitude: float = Field(
        ...,
        ge=-90,
        le=90
    )

    longitude: float = Field(
        ...,
        ge=-180,
        le=180
    )

    radius_meters: float = Field(
        default=5000,
        gt=0,
        le=50000
    )

    max_results: int = Field(
        default=10,
        ge=1,
        le=20
    )


# ============================================================
# SAVE UPLOAD
# ============================================================

async def save_upload_file(
    file: UploadFile
) -> Path:

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if file.content_type not in allowed_types:

        raise HTTPException(
            status_code=400,
            detail=(
                "Only JPG, PNG, and WEBP "
                "images are allowed."
            )
        )

    contents = await file.read()

    if not contents:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(contents) > 10 * 1024 * 1024:

        raise HTTPException(
            status_code=413,
            detail=(
                "File is too large. "
                "Maximum size is 10 MB."
            )
        )

    original_name = (
        file.filename
        or "uploaded_image"
    )

    extension = Path(
        original_name
    ).suffix.lower()

    if extension not in {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }:

        extension = ".jpg"

    file_name = (
        f"upload_{os.urandom(8).hex()}"
        f"{extension}"
    )

    file_path = (
        UPLOAD_DIR / file_name
    )

    with open(
        file_path,
        "wb"
    ) as buffer:

        buffer.write(contents)

    return file_path


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "status": "online",
        "service": "Healthcare AI Backend",
        "version": "1.0.0",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "service": "Healthcare AI Backend",
    }


# ============================================================
# MEDICATION
# ============================================================

@app.get("/medication")
def medication():

    try:

        # Lazy import
        from medication_data import (
            get_medication_data
        )

        return get_medication_data()

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Medication service error: "
                f"{error}"
            )
        )


# ============================================================
# REMINDERS
# ============================================================

@app.get("/reminders")
def reminders():

    try:

        # Lazy import
        from reminder_engine import (
            get_all_reminders
        )

        return get_all_reminders()

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Reminder service error: "
                f"{error}"
            )
        )


# ============================================================
# HEALTHCARE AI AGENT
# ============================================================

@app.post("/healthcare")
def healthcare(
    request: HealthcareRequest
):

    try:

        # VERY IMPORTANT:
        # This heavy module is imported only
        # when the endpoint is actually used.
        from healthcare_service import (
            process_healthcare
        )

        result = process_healthcare(
            question=request.question,
            symptom_text=request.symptom_text,
            image_path=""
        )

        return {
            "status": "success",
            "data": result
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Healthcare service error: "
                f"{error}"
            )
        )


# ============================================================
# SKIN ANALYSIS
# ============================================================

@app.post("/skin-analysis-upload")
async def skin_analysis_upload(
    file: UploadFile = File(...)
):

    file_path = None

    try:

        file_path = await save_upload_file(
            file
        )

        with open(
            file_path,
            "rb"
        ) as image_file:

            image_bytes = image_file.read()

        # Lazy import
        from skin_analysis import (
            analyze_skin_image
        )

        result = analyze_skin_image(
            image_bytes
        )

        return {
            "status": "success",
            "data": result
        }

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Skin analysis error: "
                f"{error}"
            )
        )

    finally:

        if (
            file_path is not None
            and file_path.exists()
        ):

            try:
                file_path.unlink()

            except Exception:
                pass


# ============================================================
# PRESCRIPTION UPLOAD
# ============================================================

@app.post("/prescription-upload")
async def prescription_upload(
    file: UploadFile = File(...),
    reminder_times: str = Form("")
):

    file_path = None

    try:

        file_path = await save_upload_file(
            file
        )

        # Lazy import
        from prescription_service import (
            process_prescription
        )

        result = process_prescription(
            image_path=str(file_path),
            reminder_times=reminder_times
        )

        return {
            "status": "success",
            "data": result
        }

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Prescription processing error: "
                f"{error}"
            )
        )

    finally:

        if (
            file_path is not None
            and file_path.exists()
        ):

            try:
                file_path.unlink()

            except Exception:
                pass


# ============================================================
# MEDICINE PHOTO
# ============================================================

@app.post("/medicine-photo")
async def medicine_photo(
    file: UploadFile = File(...)
):

    file_path = None

    try:

        file_path = await save_upload_file(
            file
        )

        # Lazy import
        from medicine_photo_service import (
            analyze_medicine_photo
        )

        result = analyze_medicine_photo(
            str(file_path)
        )

        return {
            "status": "success",
            "data": result,
            "verification_required": True,
            "safety_note": (
                "Medicine identification from an "
                "image is not confirmation that the "
                "medicine should be taken. Verify the "
                "package label and consult a pharmacist "
                "or clinician."
            )
        }

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Medicine photo analysis error: "
                f"{error}"
            )
        )

    finally:

        if (
            file_path is not None
            and file_path.exists()
        ):

            try:
                file_path.unlink()

            except Exception:
                pass


# ============================================================
# NEARBY CARE
# ============================================================

@app.post("/nearby-care")
def nearby_care(
    request: NearbyCareRequest
):

    try:

        # This module is relatively light,
        # but keeping it lazy also keeps startup small.
        from care_location_service import (
            find_nearby_care
        )

        result = find_nearby_care(
            latitude=request.latitude,
            longitude=request.longitude,
            radius_meters=request.radius_meters,
            max_results=request.max_results
        )

        return {
            "status": "success",
            "data": result
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except RuntimeError as error:

        raise HTTPException(
            status_code=502,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Nearby care service error: "
                f"{error}"
            )
        )


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,
        reload=True
    )