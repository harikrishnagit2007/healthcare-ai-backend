"""
medication_schedule_service.py

Purpose:
    Create, validate, save, update, and retrieve medication schedules.

Flow:

    Medicine
        ↓
    Start Date
        ↓
    End Date
        ↓
    Morning / Afternoon / Evening / Night
        ↓
    Exact Time
        ↓
    Repeat Days
        ↓
    User Confirmation
        ↓
    Saved Schedule
        ↓
    Alarm Engine (next module)

Safety:
    - This module does NOT prescribe medication.
    - It does NOT invent dosage.
    - It stores a schedule explicitly provided/confirmed by the user.
"""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, time
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

SCHEDULE_FILE = Path(__file__).with_name(
    "medication_schedules.json"
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_PERIODS = {
    "morning",
    "afternoon",
    "evening",
    "night",
}

VALID_DAYS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}


DAY_ORDER = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    """
    Current local timestamp for audit purposes.
    """

    return datetime.now().astimezone().isoformat()


def _normalize_text(
    value: Any,
) -> str:
    """
    Normalize text.
    """

    if value is None:
        return ""

    return " ".join(
        str(value)
        .strip()
        .split()
    )


def _parse_date(
    value: str,
) -> date:
    """
    Parse YYYY-MM-DD.
    """

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d",
        ).date()

    except ValueError as exc:
        raise ValueError(
            "Date must use YYYY-MM-DD format."
        ) from exc


def _parse_time(
    value: str,
) -> time:
    """
    Parse HH:MM using 24-hour format.
    """

    try:
        return datetime.strptime(
            value,
            "%H:%M",
        ).time()

    except ValueError as exc:
        raise ValueError(
            "Time must use HH:MM format."
        ) from exc


def _normalize_period(
    period: str,
) -> str:

    value = _normalize_text(
        period
    ).lower()

    if value not in VALID_PERIODS:

        raise ValueError(
            "Period must be one of: "
            "morning, afternoon, evening, night."
        )

    return value


def _normalize_days(
    days: list[str],
) -> list[str]:
    """
    Normalize and sort repeat days.
    """

    if not isinstance(
        days,
        list,
    ):

        raise ValueError(
            "repeat_days must be a list."
        )

    normalized = []

    for day in days:

        value = _normalize_text(
            day
        ).lower()

        if value not in VALID_DAYS:

            raise ValueError(
                f"Invalid repeat day: {day}"
            )

        if value not in normalized:
            normalized.append(value)

    normalized.sort(
        key=lambda item: DAY_ORDER[item]
    )

    if not normalized:

        raise ValueError(
            "At least one repeat day is required."
        )

    return normalized


def _generate_schedule_id() -> str:
    return (
        "med_"
        + uuid.uuid4().hex[:12]
    )


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def load_schedules() -> list[dict[str, Any]]:
    """
    Load saved medication schedules.
    """

    if not SCHEDULE_FILE.exists():

        return []

    try:

        with SCHEDULE_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

    except (
        OSError,
        json.JSONDecodeError,
    ):

        return []

    if not isinstance(
        data,
        list,
    ):

        return []

    return data


def save_schedules(
    schedules: list[dict[str, Any]],
) -> None:
    """
    Save medication schedules.
    """

    with SCHEDULE_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            schedules,
            file,
            indent=2,
            ensure_ascii=False,
        )


# ---------------------------------------------------------------------------
# Schedule validation
# ---------------------------------------------------------------------------

def validate_schedule(
    medicine_name: str,
    start_date: str,
    end_date: str | None,
    schedule_entries: list[dict[str, Any]],
    repeat_days: list[str],
) -> dict[str, Any]:
    """
    Validate all schedule information.

    schedule_entries example:

    [
        {
            "period": "morning",
            "time": "08:00"
        },
        {
            "period": "evening",
            "time": "20:00"
        }
    ]
    """

    medicine_name = _normalize_text(
        medicine_name
    )

    if not medicine_name:

        raise ValueError(
            "Medicine name cannot be empty."
        )

    start = _parse_date(
        start_date
    )

    end = None

    if end_date:

        end = _parse_date(
            end_date
        )

        if end < start:

            raise ValueError(
                "End date cannot be before start date."
            )

    if not isinstance(
        schedule_entries,
        list,
    ):

        raise ValueError(
            "schedule_entries must be a list."
        )

    if not schedule_entries:

        raise ValueError(
            "At least one medication time is required."
        )

    normalized_entries = []

    seen_times = set()

    for entry in schedule_entries:

        if not isinstance(
            entry,
            dict,
        ):

            raise ValueError(
                "Each schedule entry must be an object."
            )

        period = _normalize_period(
            entry.get("period", "")
        )

        time_value = _normalize_text(
            entry.get("time", "")
        )

        parsed_time = _parse_time(
            time_value
        )

        normalized_time = (
            parsed_time.strftime(
                "%H:%M"
            )
        )

        unique_key = (
            period,
            normalized_time,
        )

        if unique_key in seen_times:

            raise ValueError(
                "Duplicate medication time: "
                f"{period} {normalized_time}"
            )

        seen_times.add(
            unique_key
        )

        normalized_entries.append(
            {
                "period": period,
                "time": normalized_time,
            }
        )

    normalized_entries.sort(
        key=lambda entry: (
            entry["time"],
            entry["period"],
        )
    )

    normalized_days = _normalize_days(
        repeat_days
    )

    return {
        "medicine_name": medicine_name,
        "start_date": start.isoformat(),
        "end_date": (
            end.isoformat()
            if end
            else None
        ),
        "schedule_entries": normalized_entries,
        "repeat_days": normalized_days,
    }


# ---------------------------------------------------------------------------
# Create schedule
# ---------------------------------------------------------------------------

def create_medication_schedule(
    medicine_name: str,
    start_date: str,
    schedule_entries: list[dict[str, Any]],
    repeat_days: list[str],
    end_date: str | None = None,
    rxcui: str | None = None,
    confirmed_by_user: bool = False,
) -> dict[str, Any]:
    """
    Create and save a medication schedule.

    IMPORTANT:
        confirmed_by_user must be True before the schedule is
        considered active for reminders.
    """

    validated = validate_schedule(
        medicine_name=medicine_name,
        start_date=start_date,
        end_date=end_date,
        schedule_entries=schedule_entries,
        repeat_days=repeat_days,
    )

    schedule = {
        "schedule_id": _generate_schedule_id(),

        "medicine_name": validated[
            "medicine_name"
        ],

        "rxcui": (
            _normalize_text(rxcui)
            or None
        ),

        "start_date": validated[
            "start_date"
        ],

        "end_date": validated[
            "end_date"
        ],

        "schedule_entries": validated[
            "schedule_entries"
        ],

        "repeat_days": validated[
            "repeat_days"
        ],

        "confirmed_by_user": bool(
            confirmed_by_user
        ),

        "status": (
            "active"
            if confirmed_by_user
            else "pending_confirmation"
        ),

        "created_at": _now_iso(),

        "updated_at": _now_iso(),
    }

    schedules = load_schedules()

    schedules.append(
        schedule
    )

    save_schedules(
        schedules
    )

    return schedule


# ---------------------------------------------------------------------------
# Confirm existing schedule
# ---------------------------------------------------------------------------

def confirm_medication_schedule(
    schedule_id: str,
) -> dict[str, Any]:
    """
    Confirm a pending schedule.
    """

    schedule_id = _normalize_text(
        schedule_id
    )

    schedules = load_schedules()

    for schedule in schedules:

        if schedule.get(
            "schedule_id"
        ) != schedule_id:

            continue

        schedule[
            "confirmed_by_user"
        ] = True

        schedule[
            "status"
        ] = "active"

        schedule[
            "updated_at"
        ] = _now_iso()

        save_schedules(
            schedules
        )

        return schedule

    raise ValueError(
        f"Schedule not found: {schedule_id}"
    )


# ---------------------------------------------------------------------------
# Pause schedule
# ---------------------------------------------------------------------------

def pause_medication_schedule(
    schedule_id: str,
) -> dict[str, Any]:
    """
    Pause an active schedule.
    """

    schedules = load_schedules()

    for schedule in schedules:

        if schedule.get(
            "schedule_id"
        ) != schedule_id:

            continue

        schedule[
            "status"
        ] = "paused"

        schedule[
            "updated_at"
        ] = _now_iso()

        save_schedules(
            schedules
        )

        return schedule

    raise ValueError(
        f"Schedule not found: {schedule_id}"
    )


# ---------------------------------------------------------------------------
# Resume schedule
# ---------------------------------------------------------------------------

def resume_medication_schedule(
    schedule_id: str,
) -> dict[str, Any]:
    """
    Resume a previously paused schedule.
    """

    schedules = load_schedules()

    for schedule in schedules:

        if schedule.get(
            "schedule_id"
        ) != schedule_id:

            continue

        if not schedule.get(
            "confirmed_by_user",
            False,
        ):

            raise ValueError(
                "Schedule cannot be resumed "
                "before user confirmation."
            )

        schedule[
            "status"
        ] = "active"

        schedule[
            "updated_at"
        ] = _now_iso()

        save_schedules(
            schedules
        )

        return schedule

    raise ValueError(
        f"Schedule not found: {schedule_id}"
    )


# ---------------------------------------------------------------------------
# Delete schedule
# ---------------------------------------------------------------------------

def delete_medication_schedule(
    schedule_id: str,
) -> bool:
    """
    Delete one medication schedule.
    """

    schedules = load_schedules()

    original_length = len(
        schedules
    )

    schedules = [
        schedule
        for schedule in schedules
        if schedule.get(
            "schedule_id"
        ) != schedule_id
    ]

    if len(schedules) == original_length:

        return False

    save_schedules(
        schedules
    )

    return True


# ---------------------------------------------------------------------------
# Get schedule
# ---------------------------------------------------------------------------

def get_medication_schedule(
    schedule_id: str,
) -> dict[str, Any] | None:

    schedules = load_schedules()

    for schedule in schedules:

        if schedule.get(
            "schedule_id"
        ) == schedule_id:

            return schedule

    return None


# ---------------------------------------------------------------------------
# Get all schedules
# ---------------------------------------------------------------------------

def get_all_medication_schedules(
    active_only: bool = False,
) -> list[dict[str, Any]]:

    schedules = load_schedules()

    if not active_only:

        return schedules

    return [
        schedule
        for schedule in schedules
        if schedule.get(
            "status"
        ) == "active"
    ]


# ---------------------------------------------------------------------------
# Schedule summary
# ---------------------------------------------------------------------------

def build_schedule_summary(
    schedule: dict[str, Any],
) -> str:
    """
    Create a human-readable summary for the frontend.
    """

    medicine = schedule.get(
        "medicine_name",
        "Medicine",
    )

    start_date = schedule.get(
        "start_date",
        "",
    )

    end_date = schedule.get(
        "end_date"
    )

    repeat_days = schedule.get(
        "repeat_days",
        [],
    )

    status = schedule.get(
        "status",
        "unknown",
    )

    lines = [
        f"Medicine: {medicine}",
        f"Start date: {start_date}",
    ]

    if end_date:

        lines.append(
            f"End date: {end_date}"
        )

    else:

        lines.append(
            "End date: Not specified"
        )

    if repeat_days:

        formatted_days = ", ".join(
            day.title()
            for day in repeat_days
        )

        lines.append(
            f"Repeat: {formatted_days}"
        )

    lines.append(
        f"Status: {status}"
    )

    lines.append(
        "Times:"
    )

    for entry in schedule.get(
        "schedule_entries",
        [],
    ):

        period = (
            entry.get(
                "period",
                "",
            )
            .title()
        )

        time_value = entry.get(
            "time",
            "",
        )

        lines.append(
            f"  - {period}: {time_value}"
        )

    return "\n".join(
        lines
    )


# ---------------------------------------------------------------------------
# Direct test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("=" * 72)
    print(
        "MEDICATION SCHEDULE SERVICE TEST"
    )
    print("=" * 72)

    try:

        test_schedule = (
            create_medication_schedule(
                medicine_name="Paracetamol",

                start_date="2026-09-25",

                end_date=None,

                schedule_entries=[
                    {
                        "period": "morning",
                        "time": "08:00",
                    },
                    {
                        "period": "evening",
                        "time": "20:00",
                    },
                ],

                repeat_days=[
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ],

                rxcui=None,

                confirmed_by_user=True,
            )
        )

        print()
        print(
            "SCHEDULE CREATED:"
        )

        print(
            json.dumps(
                test_schedule,
                indent=2,
                ensure_ascii=False,
            )
        )

        print()
        print(
            "FRONTEND SUMMARY:"
        )

        print(
            build_schedule_summary(
                test_schedule
            )
        )

        print()
        print(
            "ALL SAVED SCHEDULES:"
        )

        print(
            json.dumps(
                get_all_medication_schedules(),
                indent=2,
                ensure_ascii=False,
            )
        )

    except Exception as exc:

        print()
        print(
            "ERROR:"
        )

        print(
            str(exc)
        )

    print()
    print("=" * 72)
    print(
        "TEST COMPLETED"
    )
    print("=" * 72)