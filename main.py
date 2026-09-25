from __future__ import annotations

import inspect
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# ============================================================
# CORE SERVICES
# ============================================================

from healthcare_service import process_healthcare

from medication_data import get_medication_data

from reminder_engine import get_all_reminders

from symptom_confirmation_service import (
    analyze_symptom_confirmation,
    record_confirmation,
    get_confirmed_symptoms,
    get_rejected_symptoms,
)

from care_location_service import (
    find_nearby_care,
    find_nearby_hospitals,
    find_nearby_pharmacies,
)

from medication_schedule_service import (
    create_medication_schedule,
    confirm_medication_schedule,
    pause_medication_schedule,
    resume_medication_schedule,
    delete_medication_schedule,
    get_medication_schedule,
    get_all_medication_schedules,
    build_schedule_summary,
)

from medication_alarm_service import (
    generate_alarms_for_date,
    generate_alarms_for_range,
    get_due_alarms,
    get_today_alarms,
    start_alarm,
    mark_alarm_taken,
    mark_alarm_skipped,
    snooze_alarm,
)

from medication_adherence_service import (
    mark_taken,
    mark_skipped,
    mark_missed,
    mark_snoozed,
    detect_missed_alarms,
    get_today_adherence,
    get_medication_history,
    get_adherence_summary,
    build_today_dashboard,
)

from health_report_service import (
    build_health_report,
)

from safety_guard_service import (
    run_safety_guard,
)

from multilingual_health_service import (
    get_language_info,
    build_multilingual_context,
)


# ============================================================
# OPTIONAL SERVICES
# ============================================================

try:
    from medicine_photo_service import analyze_medicine_photo
except Exception:
    analyze_medicine_photo = None


try:
    from skin_analysis import analyze_skin_image
except Exception:
    analyze_skin_image = None


try:
    from prescription_service import process_prescription
except Exception:
    process_prescription = None


try:
    from health_timeline_service import (
        add_timeline_event,
        get_timeline,
        get_timeline_event,
        delete_timeline_event,
    )
except Exception:
    add_timeline_event = None
    get_timeline = None
    get_timeline_event = None
    delete_timeline_event = None


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Beyond Prediction - Healthcare AI Backend",
    version="1.0.0",
    description=(
        "Context-aware Healthcare AI backend for health context, "
        "symptom support, medication management, adherence, "
        "health timelines, multilingual assistance, safety screening, "
        "care navigation and doctor handoff."
    ),
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
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# REQUEST MODELS
# ============================================================


class HealthcareRequest(BaseModel):
    question: str
    symptom_text: str = ""
    image_path: str = ""

    # Supported:
    # en = English
    # ta = Tamil
    # hi = Hindi
    # te = Telugu
    # ml = Malayalam
    language: str = "en"


class SymptomCompareRequest(BaseModel):
    previous: Any = []
    current: Any = []


class SymptomConfirmationRequest(BaseModel):
    symptom: str
    confirmed: bool


class NearbyCareRequest(BaseModel):
    latitude: float
    longitude: float
    radius_meters: int = 5000
    max_results: int = 10
    confirmed_symptoms: list[str] = Field(
        default_factory=list
    )


class MedicationScheduleRequest(BaseModel):
    medicine_name: str

    start_date: str
    end_date: Optional[str] = None

    morning: bool = False
    morning_time: str = ""

    afternoon: bool = False
    afternoon_time: str = ""

    evening: bool = False
    evening_time: str = ""

    night: bool = False
    night_time: str = ""

    repeat_days: list[str] = Field(
        default_factory=list
    )


class ScheduleConfirmationRequest(BaseModel):
    schedule_id: str


class AlarmActionRequest(BaseModel):
    alarm_id: str


class AlarmSnoozeRequest(BaseModel):
    alarm_id: str
    minutes: int = 10


class AlarmRangeRequest(BaseModel):
    start_date: str
    end_date: str


class TimelineEventRequest(BaseModel):
    event_type: str
    title: str
    details: str = ""
    source: str = "user"
    event_date: Optional[str] = None
    severity: str = "info"
    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================
# HELPERS
# ============================================================


def service_available(service: Any) -> bool:
    return callable(service)


async def save_upload(file: UploadFile) -> str:
    """
    Save an uploaded file safely.
    """

    original_name = file.filename or "upload.bin"

    suffix = Path(
        original_name
    ).suffix.lower()

    filename = (
        f"{uuid.uuid4().hex}{suffix}"
    )

    destination = (
        UPLOAD_DIR / filename
    )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    max_size = 20 * 1024 * 1024

    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=(
                "Uploaded file is too large. "
                "Maximum size is 20 MB."
            ),
        )

    destination.write_bytes(
        content
    )

    return str(destination)


def model_to_dict(
    model: BaseModel,
) -> dict[str, Any]:

    if hasattr(
        model,
        "model_dump",
    ):
        return model.model_dump()

    return model.dict()


def call_with_supported_kwargs(
    function: Any,
    payload: dict[str, Any],
) -> Any:
    """
    Call a project service while passing only
    the arguments that its current signature supports.
    """

    if not callable(function):
        raise RuntimeError(
            "Service function is unavailable."
        )

    try:
        signature = inspect.signature(
            function
        )
    except (
        TypeError,
        ValueError,
    ):
        return function(
            **payload
        )

    parameters = signature.parameters

    accepts_kwargs = any(
        parameter.kind
        == inspect.Parameter.VAR_KEYWORD
        for parameter
        in parameters.values()
    )

    if accepts_kwargs:
        return function(
            **payload
        )

    accepted = {}

    for name, value in payload.items():
        if name in parameters:
            accepted[name] = value

    return function(
        **accepted
    )


def record_timeline_event(
    event_type: str,
    title: str,
    details: str = "",
    source: str = "system",
    severity: str = "info",
    metadata: Optional[
        dict[str, Any]
    ] = None,
) -> None:
    """
    Timeline recording is intentionally non-blocking.
    A timeline failure should not break the main healthcare operation.
    """

    if not service_available(
        add_timeline_event
    ):
        return

    try:
        add_timeline_event(
            event_type=event_type,
            title=title,
            details=details,
            source=source,
            severity=severity,
            metadata=metadata or {},
        )
    except Exception:
        pass


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
# MEDICATION INFORMATION
# ============================================================


@app.get("/medication")
def medication():

    try:
        return get_medication_data()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Medication service error: {exc}"
            ),
        )


@app.get("/medications")
def medications():

    try:
        return get_medication_data()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Medication service error: {exc}"
            ),
        )


# ============================================================
# REMINDERS
# ============================================================


@app.get("/reminders")
def reminders():

    try:
        return get_all_reminders()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Reminder service error: {exc}"
            ),
        )


# ============================================================
# STANDARD HEALTHCARE AI
# ============================================================


@app.post("/healthcare")
def healthcare(
    request: HealthcareRequest,
):

    try:

        return process_healthcare(
            question=request.question,
            symptom_text=request.symptom_text,
            image_path=request.image_path,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Healthcare service error: {exc}"
            ),
        )


@app.post("/ask")
def ask(
    request: HealthcareRequest,
):

    try:

        return process_healthcare(
            question=request.question,
            symptom_text=request.symptom_text,
            image_path=request.image_path,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Healthcare service error: {exc}"
            ),
        )


# ============================================================
# SAFETY + MULTILINGUAL HEALTHCARE AI
# ============================================================


@app.post("/healthcare-safe")
def healthcare_safe(
    request: HealthcareRequest,
):
    """
    Safety-aware multilingual healthcare endpoint.

    Flow:

    User Question
        ↓
    Language Context
        ↓
    Safety Guard
        ↓
    Emergency / Urgent / Routine
        ↓
    Healthcare AI
        ↓
    Language-aware response instruction
    """

    try:

        # ----------------------------------------------------
        # 1. Language
        # ----------------------------------------------------

        language_info = get_language_info(
            request.language
        )

        # ----------------------------------------------------
        # 2. Safety screening
        # ----------------------------------------------------

        safety = run_safety_guard(
            question=request.question,
            symptom_text=request.symptom_text,
        )

        # ----------------------------------------------------
        # 3. Emergency safety response
        # ----------------------------------------------------

        if safety.get(
            "level"
        ) == "emergency":

            record_timeline_event(
                event_type="safety",
                title="Safety guard detected emergency signal",
                details=(
                    safety.get(
                        "user_message",
                        "",
                    )
                ),
                source="safety_guard_service",
                severity="urgent",
                metadata={
                    "language": language_info[
                        "code"
                    ],
                    "signals": safety.get(
                        "emergency_signals",
                        [],
                    ),
                },
            )

            return {
                "status": "safety_alert",
                "language": language_info,
                "safety": safety,
                "ai_response": None,
                "message": safety.get(
                    "user_message",
                    "Please seek urgent medical attention.",
                ),
            }

        # ----------------------------------------------------
        # 4. Build multilingual AI instruction
        # ----------------------------------------------------

        language_instruction = (
            language_info[
                "instruction"
            ]
        )

        enhanced_question = (
            f"{language_instruction}\n\n"
            f"User question:\n"
            f"{request.question}"
        )

        # ----------------------------------------------------
        # 5. Normal healthcare processing
        # ----------------------------------------------------

        result = process_healthcare(
            question=enhanced_question,
            symptom_text=request.symptom_text,
            image_path=request.image_path,
        )

        record_timeline_event(
            event_type="healthcare_ai",
            title="Safety-aware healthcare query processed",
            details=(
                f"Language: "
                f"{language_info['name']}"
            ),
            source="healthcare_safe",
            severity="info",
            metadata={
                "language": language_info[
                    "code"
                ],
                "safety_level": safety.get(
                    "level"
                ),
            },
        )

        return {
            "status": "success",
            "language": language_info,
            "safety": safety,
            "ai_response": result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Safety-aware healthcare "
                f"processing error: {exc}"
            ),
        )


# ============================================================
# LANGUAGE INFORMATION
# ============================================================


@app.get("/languages")
def languages():

    return build_multilingual_context()


@app.get("/languages/{language}")
def language_info(
    language: str,
):

    return get_language_info(
        language
    )


# ============================================================
# SYMPTOMS
# ============================================================


@app.post("/symptoms/compare")
def symptoms_compare(
    request: SymptomCompareRequest,
):

    if not service_available(
        analyze_symptom_confirmation
    ):

        raise HTTPException(
            status_code=503,
            detail=(
                "Symptom confirmation "
                "service is unavailable."
            ),
        )

    try:

        result = call_with_supported_kwargs(
            analyze_symptom_confirmation,
            {
                "previous": request.previous,
                "current": request.current,
            },
        )

        return {
            "status": "success",
            "result": result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Symptom comparison error: {exc}"
            ),
        )


@app.post("/symptoms/confirm")
def symptoms_confirm(
    request: SymptomConfirmationRequest,
):

    if not service_available(
        record_confirmation
    ):

        raise HTTPException(
            status_code=503,
            detail=(
                "Symptom confirmation "
                "storage service is unavailable."
            ),
        )

    try:

        result = call_with_supported_kwargs(
            record_confirmation,
            {
                "symptom": request.symptom,
                "confirmed": request.confirmed,
                "status": (
                    "confirmed"
                    if request.confirmed
                    else "rejected"
                ),
            },
        )

        record_timeline_event(
            event_type="symptom",
            title=(
                f"Symptom confirmed: "
                f"{request.symptom}"
                if request.confirmed
                else
                f"Symptom not confirmed: "
                f"{request.symptom}"
            ),
            details=(
                "User confirmed the symptom."
                if request.confirmed
                else
                "User did not confirm the symptom."
            ),
            source=(
                "symptom_confirmation_service"
            ),
            severity="notice",
            metadata={
                "symptom": request.symptom,
                "confirmed": request.confirmed,
            },
        )

        return {
            "status": "success",
            "symptom": request.symptom,
            "confirmed": request.confirmed,
            "result": result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Symptom confirmation "
                f"error: {exc}"
            ),
        )


@app.get("/symptoms/confirmed")
def symptoms_confirmed():

    try:

        return {
            "confirmed_symptoms":
                get_confirmed_symptoms()
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Unable to load confirmed "
                f"symptoms: {exc}"
            ),
        )


@app.get("/symptoms/rejected")
def symptoms_rejected():

    try:

        return {
            "rejected_symptoms":
                get_rejected_symptoms()
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Unable to load rejected "
                f"symptoms: {exc}"
            ),
        )


# ============================================================
# MEDICINE PHOTO
# ============================================================


@app.post("/medicine-photo")
async def medicine_photo(
    file: UploadFile = File(...),
):

    if not service_available(
        analyze_medicine_photo
    ):

        raise HTTPException(
            status_code=503,
            detail=(
                "Medicine photo service "
                "is unavailable."
            ),
        )

    image_path = await save_upload(
        file
    )

    try:

        result = analyze_medicine_photo(
            image_path
        )

        record_timeline_event(
            event_type="medicine",
            title="Medicine photo analyzed",
            details=(
                "A medicine image was submitted "
                "for analysis."
            ),
            source="medicine_photo_service",
            severity="info",
        )

        return {
            "status": "success",
            "filename": file.filename,
            "result": result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Medicine photo analysis "
                f"error: {exc}"
            ),
        )


# ============================================================
# SKIN ANALYSIS
# ============================================================


@app.post("/skin-analysis-upload")
async def skin_analysis_upload(
    file: UploadFile = File(...),
):

    if not service_available(
        analyze_skin_image
    ):

        raise HTTPException(
            status_code=503,
            detail=(
                "Skin analysis service "
                "is unavailable."
            ),
        )

    image_path = await save_upload(
        file
    )

    try:

        result = analyze_skin_image(
            image_path
        )

        record_timeline_event(
            event_type="skin_analysis",
            title="Skin image analyzed",
            details=(
                "A skin image was submitted "
                "for informational analysis."
            ),
            source="skin_analysis_service",
            severity="info",
        )

        return {
            "status": "success",
            "filename": file.filename,
            "result": result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Skin analysis error: {exc}"
            ),
        )


# ============================================================
# PRESCRIPTION
# ============================================================


@app.post("/prescription-upload")
async def prescription_upload(
    file: UploadFile = File(...),
):

    if not service_available(
        process_prescription
    ):

        raise HTTPException(
            status_code=503,
            detail=(
                "Prescription service "
                "is unavailable."
            ),
        )

    image_path = await save_upload(
        file
    )

    try:

        result = process_prescription(
            image_path
        )

        record_timeline_event(
            event_type="prescription",
            title="Prescription uploaded",
            details=(
                "Prescription image submitted "
                "for processing."
            ),
            source="prescription_service",
            severity="info",
        )

        return {
            "status": "success",
            "filename": file.filename,
            "result": result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Prescription processing "
                f"error: {exc}"
            ),
        )


# ============================================================
# NEARBY CARE
# ============================================================


@app.post("/nearby-care")
def nearby_care(
    request: NearbyCareRequest,
):

    try:

        result = find_nearby_care(
            latitude=request.latitude,
            longitude=request.longitude,
            confirmed_symptoms=(
                request.confirmed_symptoms
            ),
            radius_meters=(
                request.radius_meters
            ),
            max_results=(
                request.max_results
            ),
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Nearby care error: {exc}"
            ),
        )


@app.get("/nearby-care")
def nearby_care_get(
    latitude: float,
    longitude: float,
    radius_meters: int = 5000,
    max_results: int = 10,
):

    try:

        return find_nearby_care(
            latitude=latitude,
            longitude=longitude,
            confirmed_symptoms=[],
            radius_meters=radius_meters,
            max_results=max_results,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Nearby care error: {exc}"
            ),
        )


@app.get("/nearby-hospitals")
def nearby_hospitals(
    latitude: float,
    longitude: float,
    radius_meters: int = 5000,
    max_results: int = 10,
):

    try:

        return find_nearby_hospitals(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            max_results=max_results,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Nearby hospital error: {exc}"
            ),
        )


@app.get("/nearby-pharmacies")
def nearby_pharmacies(
    latitude: float,
    longitude: float,
    radius_meters: int = 5000,
    max_results: int = 10,
):

    try:

        return find_nearby_pharmacies(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            max_results=max_results,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Nearby pharmacy error: {exc}"
            ),
        )


# ============================================================
# MEDICATION SCHEDULE
# ============================================================


@app.post("/medication-schedule")
def medication_schedule(
    request: MedicationScheduleRequest,
):

    try:

        result = call_with_supported_kwargs(
            create_medication_schedule,
            model_to_dict(request),
        )

        record_timeline_event(
            event_type="medication",
            title=(
                "Medication schedule created: "
                f"{request.medicine_name}"
            ),
            details=(
                f"Start: {request.start_date}; "
                f"End: "
                f"{request.end_date or 'not specified'}"
            ),
            source=(
                "medication_schedule_service"
            ),
            severity="info",
            metadata=model_to_dict(
                request
            ),
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Medication schedule "
                f"error: {exc}"
            ),
        )


@app.get("/medication-schedules")
def medication_schedules():

    try:

        return (
            get_all_medication_schedules()
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Medication schedule retrieval "
                f"error: {exc}"
            ),
        )


@app.get(
    "/medication-schedule/{schedule_id}"
)
def medication_schedule_get(
    schedule_id: str,
):

    try:

        result = get_medication_schedule(
            schedule_id
        )

        if result is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Medication schedule "
                    "not found."
                ),
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Medication schedule "
                f"error: {exc}"
            ),
        )


@app.post(
    "/medication-schedule/confirm"
)
def medication_schedule_confirm(
    request: ScheduleConfirmationRequest,
):

    try:

        result = (
            confirm_medication_schedule(
                request.schedule_id
            )
        )

        record_timeline_event(
            event_type="medication",
            title="Medication schedule confirmed",
            details=(
                f"Schedule ID: "
                f"{request.schedule_id}"
            ),
            source=(
                "medication_schedule_service"
            ),
            severity="info",
            metadata={
                "schedule_id":
                    request.schedule_id,
                "action": "confirm",
            },
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Schedule confirmation "
                f"error: {exc}"
            ),
        )


@app.post(
    "/medication-schedule/pause"
)
def medication_schedule_pause(
    request: ScheduleConfirmationRequest,
):

    try:

        return pause_medication_schedule(
            request.schedule_id
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Schedule pause "
                f"error: {exc}"
            ),
        )


@app.post(
    "/medication-schedule/resume"
)
def medication_schedule_resume(
    request: ScheduleConfirmationRequest,
):

    try:

        return resume_medication_schedule(
            request.schedule_id
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Schedule resume "
                f"error: {exc}"
            ),
        )


@app.delete(
    "/medication-schedule/{schedule_id}"
)
def medication_schedule_delete(
    schedule_id: str,
):

    try:

        return delete_medication_schedule(
            schedule_id
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Schedule deletion "
                f"error: {exc}"
            ),
        )


# ============================================================
# MEDICATION ALARMS
# ============================================================


@app.post(
    "/medication-alarms/generate-today"
)
def medication_alarms_generate_today():

    try:

        result = generate_alarms_for_date(
            date.today().isoformat()
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Alarm generation "
                f"error: {exc}"
            ),
        )


@app.post(
    "/medication-alarms/generate-range"
)
def medication_alarms_generate_range(
    request: AlarmRangeRequest,
):

    try:

        return generate_alarms_for_range(
            request.start_date,
            request.end_date,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Alarm range generation "
                f"error: {exc}"
            ),
        )


@app.get(
    "/medication-alarms/today"
)
def medication_alarms_today():

    try:

        return get_today_alarms()

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Today's alarm retrieval "
                f"error: {exc}"
            ),
        )


@app.get(
    "/medication-alarms/due"
)
def medication_alarms_due():

    try:

        return get_due_alarms()

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Due alarm retrieval "
                f"error: {exc}"
            ),
        )


@app.post(
    "/medication-alarm/start"
)
def medication_alarm_start(
    request: AlarmActionRequest,
):

    try:

        return start_alarm(
            request.alarm_id
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Alarm start error: {exc}"
            ),
        )


@app.post(
    "/medication-alarm/take"
)
def medication_alarm_take(
    request: AlarmActionRequest,
):

    try:

        alarm_result = (
            mark_alarm_taken(
                request.alarm_id
            )
        )

        adherence_result = (
            mark_taken(
                request.alarm_id
            )
        )

        record_timeline_event(
            event_type="adherence",
            title="Medication marked as taken",
            details=(
                f"Alarm ID: "
                f"{request.alarm_id}"
            ),
            source=(
                "medication_adherence_service"
            ),
            severity="info",
            metadata={
                "alarm_id":
                    request.alarm_id,
                "status": "taken",
            },
        )

        return {
            "alarm": alarm_result,
            "adherence": adherence_result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Medication take "
                f"action error: {exc}"
            ),
        )


@app.post(
    "/medication-alarm/snooze"
)
def medication_alarm_snooze(
    request: AlarmSnoozeRequest,
):

    try:

        alarm_result = snooze_alarm(
            request.alarm_id,
            request.minutes,
        )

        adherence_result = (
            mark_snoozed(
                request.alarm_id
            )
        )

        record_timeline_event(
            event_type="adherence",
            title="Medication alarm snoozed",
            details=(
                f"Alarm ID: "
                f"{request.alarm_id}; "
                f"Snooze: "
                f"{request.minutes} minutes"
            ),
            source=(
                "medication_adherence_service"
            ),
            severity="notice",
            metadata={
                "alarm_id":
                    request.alarm_id,
                "minutes":
                    request.minutes,
                "status": "snoozed",
            },
        )

        return {
            "alarm": alarm_result,
            "adherence":
                adherence_result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Medication snooze "
                f"error: {exc}"
            ),
        )


@app.post(
    "/medication-alarm/skip"
)
def medication_alarm_skip(
    request: AlarmActionRequest,
):

    try:

        alarm_result = (
            mark_alarm_skipped(
                request.alarm_id
            )
        )

        adherence_result = (
            mark_skipped(
                request.alarm_id
            )
        )

        record_timeline_event(
            event_type="adherence",
            title="Medication marked as skipped",
            details=(
                f"Alarm ID: "
                f"{request.alarm_id}"
            ),
            source=(
                "medication_adherence_service"
            ),
            severity="notice",
            metadata={
                "alarm_id":
                    request.alarm_id,
                "status": "skipped",
            },
        )

        return {
            "alarm": alarm_result,
            "adherence":
                adherence_result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Medication skip "
                f"action error: {exc}"
            ),
        )


# ============================================================
# MEDICATION ADHERENCE
# ============================================================


@app.post(
    "/medication-adherence/detect-missed"
)
def medication_adherence_detect_missed():

    try:

        return detect_missed_alarms()

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Missed alarm detection "
                f"error: {exc}"
            ),
        )


@app.get(
    "/medication-adherence/today"
)
def medication_adherence_today():

    try:

        return get_today_adherence()

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Today's adherence "
                f"error: {exc}"
            ),
        )


@app.get(
    "/medication-adherence/history"
)
def medication_adherence_history(
    medicine_name: Optional[str] = None,
):

    try:

        if medicine_name:

            return get_medication_history(
                medicine_name
            )

        return get_medication_history()

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Medication history "
                f"error: {exc}"
            ),
        )


@app.get(
    "/medication-adherence/summary"
)
def medication_adherence_summary():

    try:

        return get_adherence_summary()

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Adherence summary "
                f"error: {exc}"
            ),
        )


@app.get(
    "/medication-dashboard"
)
def medication_dashboard():

    try:

        return build_today_dashboard()

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Medication dashboard "
                f"error: {exc}"
            ),
        )


# ============================================================
# HEALTH TIMELINE
# ============================================================


@app.get(
    "/health-timeline"
)
def health_timeline(
    limit: int = 100,
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):

    if not service_available(
        get_timeline
    ):

        return {
            "status": "unavailable",
            "events": [],
            "count": 0,
            "message": (
                "Health timeline service "
                "is not available."
            ),
        }

    try:

        events = get_timeline(
            limit=limit,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "status": "success",
            "events": events,
            "count": len(events),
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Health timeline "
                f"error: {exc}"
            ),
        )


@app.post(
    "/health-timeline"
)
def health_timeline_add(
    request: TimelineEventRequest,
):

    if not service_available(
        add_timeline_event
    ):

        raise HTTPException(
            status_code=503,
            detail=(
                "Health timeline service "
                "is unavailable."
            ),
        )

    try:

        result = add_timeline_event(
            event_type=request.event_type,
            title=request.title,
            details=request.details,
            source=request.source,
            event_date=request.event_date,
            severity=request.severity,
            metadata=request.metadata,
        )

        return {
            "status": "success",
            "event": result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Health timeline "
                f"creation error: {exc}"
            ),
        )


@app.get(
    "/health-timeline/{event_id}"
)
def health_timeline_event(
    event_id: str,
):

    if not service_available(
        get_timeline_event
    ):

        raise HTTPException(
            status_code=503,
            detail=(
                "Health timeline service "
                "is unavailable."
            ),
        )

    try:

        result = get_timeline_event(
            event_id
        )

        if result is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Timeline event "
                    "not found."
                ),
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Health timeline "
                f"error: {exc}"
            ),
        )


@app.delete(
    "/health-timeline/{event_id}"
)
def health_timeline_delete(
    event_id: str,
):

    if not service_available(
        delete_timeline_event
    ):

        raise HTTPException(
            status_code=503,
            detail=(
                "Health timeline service "
                "is unavailable."
            ),
        )

    try:

        deleted = delete_timeline_event(
            event_id
        )

        if not deleted:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Timeline event "
                    "not found."
                ),
            )

        return {
            "status": "success",
            "deleted": True,
            "event_id": event_id,
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Timeline deletion "
                f"error: {exc}"
            ),
        )


# ============================================================
# AI HEALTH REPORT CARD
# ============================================================


@app.get(
    "/health-report"
)
def health_report():

    try:

        report = build_health_report()

        return {
            "status": "success",
            "report": report,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Health report generation "
                f"error: {exc}"
            ),
        )


# ============================================================
# SYSTEM SUMMARY
# ============================================================


@app.get(
    "/system-summary"
)
def system_summary():

    return {
        "service": (
            "Beyond Prediction - "
            "Healthcare AI Backend"
        ),
        "status": "online",

        "modules": {
            "healthcare_ai": True,
            "safety_guard": True,
            "multilingual_assistant": True,
            "symptom_confirmation": True,
            "medicine_photo":
                service_available(
                    analyze_medicine_photo
                ),
            "skin_analysis":
                service_available(
                    analyze_skin_image
                ),
            "prescription_analysis":
                service_available(
                    process_prescription
                ),
            "care_navigation": True,
            "medication_schedule": True,
            "medication_alarm": True,
            "medication_adherence": True,
            "health_timeline":
                service_available(
                    get_timeline
                ),
            "health_report": True,
        },
    }


# ============================================================
# DEVELOPMENT SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
    )