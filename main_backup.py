from __future__ import annotations

import inspect
import os
import uuid
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
# APP CONFIGURATION
# ============================================================

app = FastAPI(
    title="Beyond Prediction - Healthcare AI Backend",
    version="1.0.0",
    description=(
        "Context-aware Healthcare AI backend for health context, "
        "symptom support, medication management, adherence, "
        "health timelines, care navigation and doctor handoff."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# PYDANTIC MODELS
# ============================================================


class HealthcareRequest(BaseModel):
    question: str
    symptom_text: str = ""
    image_path: str = ""


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
    confirmed_symptoms: list[str] = Field(default_factory=list)


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

    repeat_days: list[str] = Field(default_factory=list)


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
    metadata: dict[str, Any] = Field(default_factory=dict)


class TimelineDeleteRequest(BaseModel):
    event_id: str


# ============================================================
# HELPERS
# ============================================================


def _service_available(service: Any) -> bool:
    return callable(service)


async def _save_upload(file: UploadFile) -> str:
    """
    Save an uploaded file with a generated filename.
    """

    original_name = file.filename or "upload.bin"
    suffix = Path(original_name).suffix.lower()

    safe_name = f"{uuid.uuid4().hex}{suffix}"
    destination = UPLOAD_DIR / safe_name

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Uploaded file is too large. Maximum size is 20 MB.",
        )

    destination.write_bytes(content)

    return str(destination)


def _call_with_supported_kwargs(
    function: Any,
    payload: dict[str, Any],
) -> Any:
    """
    Call an existing service while only passing parameters
    that are supported by its signature.

    This makes the FastAPI layer more tolerant of small
    signature differences between project modules.
    """

    if not callable(function):
        raise RuntimeError("Service function is unavailable.")

    try:
        signature = inspect.signature(function)
    except (TypeError, ValueError):
        return function(**payload)

    parameters = signature.parameters

    accepted_kwargs: dict[str, Any] = {}

    has_var_kwargs = any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )

    if has_var_kwargs:
        accepted_kwargs = payload
    else:
        for name, value in payload.items():
            if name in parameters:
                accepted_kwargs[name] = value

    try:
        return function(**accepted_kwargs)

    except TypeError:
        # Fallback for functions that use slightly different names.
        aliases = {
            "schedule_id": ["id"],
            "alarm_id": ["id"],
            "target_date": ["date_value", "date"],
            "start_date": ["from_date"],
            "end_date": ["to_date"],
        }

        retry_payload = dict(accepted_kwargs)

        for original_name, alias_names in aliases.items():
            if original_name not in parameters:
                if original_name not in retry_payload:
                    continue

                value = retry_payload.pop(original_name)

                for alias in alias_names:
                    if alias in parameters:
                        retry_payload[alias] = value
                        break

        return function(**retry_payload)


def _record_timeline_event(
    event_type: str,
    title: str,
    details: str = "",
    source: str = "system",
    severity: str = "info",
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """
    Record a timeline event without allowing timeline failures
    to break the primary healthcare operation.
    """

    if not _service_available(add_timeline_event):
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


def _model_dump(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()

    return model.dict()


# ============================================================
# ROOT / HEALTH
# ============================================================


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Healthcare AI Backend",
        "version": "1.0.0",
    }


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
            detail=f"Medication service error: {exc}",
        )


@app.get("/medications")
def medications():
    try:
        return get_medication_data()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Medication service error: {exc}",
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
            detail=f"Reminder service error: {exc}",
        )


# ============================================================
# HEALTHCARE AI
# ============================================================


@app.post("/healthcare")
def healthcare(request: HealthcareRequest):
    try:
        return process_healthcare(
            question=request.question,
            symptom_text=request.symptom_text,
            image_path=request.image_path,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Healthcare service error: {exc}",
        )


@app.post("/ask")
def ask(request: HealthcareRequest):
    try:
        return process_healthcare(
            question=request.question,
            symptom_text=request.symptom_text,
            image_path=request.image_path,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Healthcare service error: {exc}",
        )


# ============================================================
# SYMPTOM SUPPORT
# ============================================================


@app.post("/symptoms/compare")
def symptoms_compare(request: SymptomCompareRequest):
    if not _service_available(analyze_symptom_confirmation):
        raise HTTPException(
            status_code=503,
            detail="Symptom confirmation service is unavailable.",
        )

    payload = {
        "previous": request.previous,
        "current": request.current,
    }

    try:
        result = _call_with_supported_kwargs(
            analyze_symptom_confirmation,
            payload,
        )

        return {
            "status": "success",
            "result": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Symptom comparison error: {exc}",
        )


@app.post("/symptoms/confirm")
def symptoms_confirm(
    request: SymptomConfirmationRequest,
):
    if not _service_available(record_confirmation):
        raise HTTPException(
            status_code=503,
            detail="Symptom confirmation storage service is unavailable.",
        )

    payload = {
        "symptom": request.symptom,
        "confirmed": request.confirmed,
        "status": "confirmed" if request.confirmed else "rejected",
    }

    try:
        result = _call_with_supported_kwargs(
            record_confirmation,
            payload,
        )

        _record_timeline_event(
            event_type="symptom",
            title=(
                f"Symptom confirmed: {request.symptom}"
                if request.confirmed
                else f"Symptom rejected: {request.symptom}"
            ),
            details=(
                "User confirmed the symptom as currently experienced."
                if request.confirmed
                else "User did not confirm the symptom."
            ),
            source="symptom_confirmation_service",
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
            detail=f"Symptom confirmation error: {exc}",
        )


@app.get("/symptoms/confirmed")
def symptoms_confirmed():
    try:
        return {
            "confirmed_symptoms": get_confirmed_symptoms(),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load confirmed symptoms: {exc}",
        )


@app.get("/symptoms/rejected")
def symptoms_rejected():
    try:
        return {
            "rejected_symptoms": get_rejected_symptoms(),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load rejected symptoms: {exc}",
        )


# ============================================================
# MEDICINE PHOTO
# ============================================================


@app.post("/medicine-photo")
async def medicine_photo(
    file: UploadFile = File(...),
):
    if not _service_available(analyze_medicine_photo):
        raise HTTPException(
            status_code=503,
            detail="Medicine photo service is unavailable.",
        )

    image_path = await _save_upload(file)

    try:
        result = analyze_medicine_photo(image_path)

        _record_timeline_event(
            event_type="medicine",
            title="Medicine photo analyzed",
            details="A medicine image was submitted for analysis.",
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
            detail=f"Medicine photo analysis error: {exc}",
        )


# ============================================================
# SKIN ANALYSIS
# ============================================================


@app.post("/skin-analysis-upload")
async def skin_analysis_upload(
    file: UploadFile = File(...),
):
    if not _service_available(analyze_skin_image):
        raise HTTPException(
            status_code=503,
            detail="Skin analysis service is unavailable.",
        )

    image_path = await _save_upload(file)

    try:
        result = analyze_skin_image(image_path)

        _record_timeline_event(
            event_type="skin_analysis",
            title="Skin image analyzed",
            details="A skin image was submitted for informational analysis.",
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
            detail=f"Skin analysis error: {exc}",
        )


# ============================================================
# PRESCRIPTION ANALYSIS
# ============================================================


@app.post("/prescription-upload")
async def prescription_upload(
    file: UploadFile = File(...),
):
    if not _service_available(process_prescription):
        raise HTTPException(
            status_code=503,
            detail="Prescription service is unavailable.",
        )

    image_path = await _save_upload(file)

    try:
        result = process_prescription(image_path)

        _record_timeline_event(
            event_type="prescription",
            title="Prescription uploaded",
            details="A prescription image was submitted for processing.",
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
            detail=f"Prescription processing error: {exc}",
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
            confirmed_symptoms=request.confirmed_symptoms,
            radius_meters=request.radius_meters,
            max_results=request.max_results,
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Nearby care error: {exc}",
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
            detail=f"Nearby care error: {exc}",
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
            detail=f"Nearby hospital error: {exc}",
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
            detail=f"Nearby pharmacy error: {exc}",
        )


# ============================================================
# MEDICATION SCHEDULE
# ============================================================


@app.post("/medication-schedule")
def medication_schedule(
    request: MedicationScheduleRequest,
):
    payload = _model_dump(request)

    try:
        result = _call_with_supported_kwargs(
            create_medication_schedule,
            payload,
        )

        _record_timeline_event(
            event_type="medication",
            title=(
                f"Medication schedule created: "
                f"{request.medicine_name}"
            ),
            details=(
                f"Start: {request.start_date}; "
                f"End: {request.end_date or 'not specified'}"
            ),
            source="medication_schedule_service",
            severity="info",
            metadata=payload,
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Medication schedule error: {exc}",
        )


@app.get("/medication-schedules")
def medication_schedules():
    try:
        return get_all_medication_schedules()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Medication schedule retrieval error: {exc}",
        )


@app.get("/medication-schedule/{schedule_id}")
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
                detail="Medication schedule not found.",
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Medication schedule error: {exc}",
        )


@app.post("/medication-schedule/confirm")
def medication_schedule_confirm(
    request: ScheduleConfirmationRequest,
):
    try:
        result = confirm_medication_schedule(
            request.schedule_id
        )

        _record_timeline_event(
            event_type="medication",
            title="Medication schedule confirmed",
            details=(
                f"Schedule ID: {request.schedule_id}"
            ),
            source="medication_schedule_service",
            severity="info",
            metadata={
                "schedule_id": request.schedule_id,
                "action": "confirm",
            },
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Schedule confirmation error: {exc}",
        )


@app.post("/medication-schedule/pause")
def medication_schedule_pause(
    request: ScheduleConfirmationRequest,
):
    try:
        result = pause_medication_schedule(
            request.schedule_id
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Schedule pause error: {exc}",
        )


@app.post("/medication-schedule/resume")
def medication_schedule_resume(
    request: ScheduleConfirmationRequest,
):
    try:
        result = resume_medication_schedule(
            request.schedule_id
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Schedule resume error: {exc}",
        )


@app.delete("/medication-schedule/{schedule_id}")
def medication_schedule_delete(
    schedule_id: str,
):
    try:
        result = delete_medication_schedule(
            schedule_id
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Schedule deletion error: {exc}",
        )


# ============================================================
# MEDICATION ALARMS
# ============================================================


@app.post("/medication-alarms/generate-today")
def medication_alarms_generate_today():

    from datetime import date

    try:
        result = generate_alarms_for_date(
            date.today().isoformat()
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Alarm generation error: {exc}",
        )


@app.post("/medication-alarms/generate-range")
def medication_alarms_generate_range(
    request: AlarmRangeRequest,
):
    try:
        result = generate_alarms_for_range(
            request.start_date,
            request.end_date,
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Alarm range generation error: {exc}",
        )


@app.get("/medication-alarms/today")
def medication_alarms_today():
    try:
        return get_today_alarms()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Today's alarm retrieval error: {exc}",
        )


@app.get("/medication-alarms/due")
def medication_alarms_due():
    try:
        return get_due_alarms()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Due alarm retrieval error: {exc}",
        )


@app.post("/medication-alarm/start")
def medication_alarm_start(
    request: AlarmActionRequest,
):
    try:
        result = start_alarm(
            request.alarm_id
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Alarm start error: {exc}",
        )


@app.post("/medication-alarm/take")
def medication_alarm_take(
    request: AlarmActionRequest,
):
    try:
        alarm_result = mark_alarm_taken(
            request.alarm_id
        )

        adherence_result = mark_taken(
            request.alarm_id
        )

        _record_timeline_event(
            event_type="adherence",
            title="Medication marked as taken",
            details=(
                f"Alarm ID: {request.alarm_id}"
            ),
            source="medication_adherence_service",
            severity="info",
            metadata={
                "alarm_id": request.alarm_id,
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
            detail=f"Medication take action error: {exc}",
        )


@app.post("/medication-alarm/snooze")
def medication_alarm_snooze(
    request: AlarmSnoozeRequest,
):
    try:
        result = snooze_alarm(
            request.alarm_id,
            request.minutes,
        )

        adherence_result = mark_snoozed(
            request.alarm_id,
        )

        _record_timeline_event(
            event_type="adherence",
            title="Medication alarm snoozed",
            details=(
                f"Alarm ID: {request.alarm_id}; "
                f"Snooze: {request.minutes} minutes"
            ),
            source="medication_adherence_service",
            severity="notice",
            metadata={
                "alarm_id": request.alarm_id,
                "minutes": request.minutes,
                "status": "snoozed",
            },
        )

        return {
            "alarm": result,
            "adherence": adherence_result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Medication snooze error: {exc}",
        )


@app.post("/medication-alarm/skip")
def medication_alarm_skip(
    request: AlarmActionRequest,
):
    try:
        alarm_result = mark_alarm_skipped(
            request.alarm_id
        )

        adherence_result = mark_skipped(
            request.alarm_id
        )

        _record_timeline_event(
            event_type="adherence",
            title="Medication marked as skipped",
            details=(
                f"Alarm ID: {request.alarm_id}"
            ),
            source="medication_adherence_service",
            severity="notice",
            metadata={
                "alarm_id": request.alarm_id,
                "status": "skipped",
            },
        )

        return {
            "alarm": alarm_result,
            "adherence": adherence_result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Medication skip action error: {exc}",
        )


# ============================================================
# MEDICATION ADHERENCE
# ============================================================


@app.post("/medication-adherence/detect-missed")
def medication_adherence_detect_missed():
    try:
        result = detect_missed_alarms()

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Missed alarm detection error: {exc}",
        )


@app.get("/medication-adherence/today")
def medication_adherence_today():
    try:
        return get_today_adherence()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Today's adherence error: {exc}",
        )


@app.get("/medication-adherence/history")
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
            detail=f"Medication history error: {exc}",
        )


@app.get("/medication-adherence/summary")
def medication_adherence_summary():
    try:
        return get_adherence_summary()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Adherence summary error: {exc}",
        )


@app.get("/medication-dashboard")
def medication_dashboard():
    try:
        return build_today_dashboard()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Medication dashboard error: {exc}",
        )


# ============================================================
# HEALTH TIMELINE
# ============================================================


@app.get("/health-timeline")
def health_timeline(
    limit: int = 100,
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    if not _service_available(get_timeline):
        return {
            "status": "unavailable",
            "events": [],
            "message": (
                "Health timeline service is not available."
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
            detail=f"Health timeline error: {exc}",
        )


@app.post("/health-timeline")
def health_timeline_add(
    request: TimelineEventRequest,
):
    if not _service_available(add_timeline_event):
        raise HTTPException(
            status_code=503,
            detail="Health timeline service is unavailable.",
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
            detail=f"Health timeline creation error: {exc}",
        )


@app.get("/health-timeline/{event_id}")
def health_timeline_event(
    event_id: str,
):
    if not _service_available(get_timeline_event):
        raise HTTPException(
            status_code=503,
            detail="Health timeline service is unavailable.",
        )

    try:
        result = get_timeline_event(event_id)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Timeline event not found.",
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Health timeline error: {exc}",
        )


@app.delete("/health-timeline/{event_id}")
def health_timeline_delete(
    event_id: str,
):
    if not _service_available(delete_timeline_event):
        raise HTTPException(
            status_code=503,
            detail="Health timeline service is unavailable.",
        )

    try:
        deleted = delete_timeline_event(event_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Timeline event not found.",
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
            detail=f"Timeline deletion error: {exc}",
        )


# ============================================================
# AI HEALTH REPORT CARD
# ============================================================


@app.get("/health-report")
def health_report():
    """
    Generate the current AI Health Report Card.

    The report summarizes recorded information and is not
    a confirmed diagnosis or prescription.
    """

    try:
        report = build_health_report()

        return {
            "status": "success",
            "report": report,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Health report generation error: {exc}",
        )


# ============================================================
# FULL SYSTEM SUMMARY
# ============================================================


@app.get("/system-summary")
def system_summary():

    timeline_available = _service_available(
        get_timeline
    )

    medicine_service_available = _service_available(
        analyze_medicine_photo
    )

    skin_service_available = _service_available(
        analyze_skin_image
    )

    prescription_service_available = _service_available(
        process_prescription
    )

    return {
        "service": "Beyond Prediction - Healthcare AI Backend",
        "status": "online",

        "modules": {
            "healthcare_ai": True,
            "symptom_confirmation": True,
            "medicine_photo": medicine_service_available,
            "skin_analysis": skin_service_available,
            "prescription_analysis": prescription_service_available,
            "care_navigation": True,
            "medication_schedule": True,
            "medication_alarm": True,
            "medication_adherence": True,
            "health_timeline": timeline_available,
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