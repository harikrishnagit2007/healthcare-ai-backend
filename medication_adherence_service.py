"""
medication_adherence_service.py

Purpose:
    Track medication reminder outcomes.

States:
    - taken
    - skipped
    - missed
    - snoozed

This module records user actions and reminder history.

It does NOT:
    - prescribe medicines
    - change dosage
    - decide whether a medicine should be taken
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

ALARM_FILE = (
    BASE_DIR / "medication_alarms.json"
)

ADHERENCE_FILE = (
    BASE_DIR / "medication_adherence.json"
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STATUS_TAKEN = "taken"
STATUS_SKIPPED = "skipped"
STATUS_MISSED = "missed"
STATUS_SNOOZED = "snoozed"

VALID_OUTCOMES = {
    STATUS_TAKEN,
    STATUS_SKIPPED,
    STATUS_MISSED,
    STATUS_SNOOZED,
}


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------

def _now() -> datetime:
    """Return timezone-aware local datetime."""
    return datetime.now().astimezone()


def _now_iso() -> str:
    return _now().isoformat()


def _utc_now_iso() -> str:
    """Return timezone-aware UTC timestamp."""
    return datetime.now(
        timezone.utc
    ).isoformat()


# ---------------------------------------------------------------------------
# JSON storage
# ---------------------------------------------------------------------------

def _load_list(
    file_path: Path,
) -> list[dict[str, Any]]:
    """Load a JSON list safely."""

    if not file_path.exists():
        return []

    try:

        with file_path.open(
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


def _save_list(
    file_path: Path,
    data: list[dict[str, Any]],
) -> None:
    """Save a JSON list."""

    with file_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def load_alarms() -> list[dict[str, Any]]:
    """Load medication alarms."""

    return _load_list(
        ALARM_FILE
    )


def load_adherence_records() -> list[dict[str, Any]]:
    """Load medication adherence records."""

    return _load_list(
        ADHERENCE_FILE
    )


def save_adherence_records(
    records: list[dict[str, Any]],
) -> None:

    _save_list(
        ADHERENCE_FILE,
        records,
    )


# ---------------------------------------------------------------------------
# Record creation
# ---------------------------------------------------------------------------

def _create_record(
    alarm: dict[str, Any],
    outcome: str,
    action_source: str = "system",
) -> dict[str, Any]:
    """
    Convert an alarm into an adherence record.
    """

    if outcome not in VALID_OUTCOMES:
        raise ValueError(
            f"Invalid adherence outcome: {outcome}"
        )

    return {
        "alarm_id": alarm.get(
            "alarm_id"
        ),

        "schedule_id": alarm.get(
            "schedule_id"
        ),

        "medicine_name": alarm.get(
            "medicine_name",
            "Medicine",
        ),

        "rxcui": alarm.get(
            "rxcui"
        ),

        "alarm_date": alarm.get(
            "alarm_date"
        ),

        "alarm_time": alarm.get(
            "alarm_time"
        ),

        "period": alarm.get(
            "period"
        ),

        "outcome": outcome,

        "action_source": action_source,

        "snooze_count": alarm.get(
            "snooze_count",
            0,
        ),

        "scheduled_at": alarm.get(
            "scheduled_at"
        ),

        "recorded_at": _now_iso(),

        "recorded_at_utc": _utc_now_iso(),
    }


# ---------------------------------------------------------------------------
# Find existing record
# ---------------------------------------------------------------------------

def _find_record_for_alarm(
    records: list[dict[str, Any]],
    alarm_id: str,
) -> dict[str, Any] | None:

    for record in records:

        if record.get(
            "alarm_id"
        ) == alarm_id:

            return record

    return None


# ---------------------------------------------------------------------------
# Save / update adherence
# ---------------------------------------------------------------------------

def record_adherence(
    alarm_id: str,
    outcome: str,
    action_source: str = "user",
) -> dict[str, Any]:
    """
    Record an adherence outcome for an alarm.

    Examples:
        record_adherence("alarm_x", "taken")
        record_adherence("alarm_x", "skipped")
        record_adherence("alarm_x", "missed")
    """

    outcome = str(
        outcome
    ).strip().lower()

    if outcome not in VALID_OUTCOMES:

        raise ValueError(
            "Outcome must be one of: "
            "taken, skipped, missed, snoozed."
        )

    alarm_id = str(
        alarm_id
    ).strip()

    if not alarm_id:

        raise ValueError(
            "alarm_id cannot be empty."
        )

    alarms = load_alarms()

    alarm = None

    for item in alarms:

        if item.get(
            "alarm_id"
        ) == alarm_id:

            alarm = item
            break

    if alarm is None:

        raise ValueError(
            f"Alarm not found: {alarm_id}"
        )

    records = load_adherence_records()

    existing = _find_record_for_alarm(
        records,
        alarm_id,
    )

    # -------------------------------------------------------
    # Update existing record
    # -------------------------------------------------------

    if existing is not None:

        existing[
            "outcome"
        ] = outcome

        existing[
            "action_source"
        ] = action_source

        existing[
            "recorded_at"
        ] = _now_iso()

        existing[
            "recorded_at_utc"
        ] = _utc_now_iso()

        existing[
            "snooze_count"
        ] = alarm.get(
            "snooze_count",
            0,
        )

        record = existing

    # -------------------------------------------------------
    # Create record
    # -------------------------------------------------------

    else:

        record = _create_record(
            alarm=alarm,
            outcome=outcome,
            action_source=action_source,
        )

        records.append(
            record
        )

    save_adherence_records(
        records
    )

    return record


# ---------------------------------------------------------------------------
# Mark taken
# ---------------------------------------------------------------------------

def mark_taken(
    alarm_id: str,
) -> dict[str, Any]:

    return record_adherence(
        alarm_id=alarm_id,
        outcome=STATUS_TAKEN,
        action_source="user",
    )


# ---------------------------------------------------------------------------
# Mark skipped
# ---------------------------------------------------------------------------

def mark_skipped(
    alarm_id: str,
) -> dict[str, Any]:

    return record_adherence(
        alarm_id=alarm_id,
        outcome=STATUS_SKIPPED,
        action_source="user",
    )


# ---------------------------------------------------------------------------
# Mark missed
# ---------------------------------------------------------------------------

def mark_missed(
    alarm_id: str,
) -> dict[str, Any]:

    return record_adherence(
        alarm_id=alarm_id,
        outcome=STATUS_MISSED,
        action_source="system",
    )


# ---------------------------------------------------------------------------
# Record snooze
# ---------------------------------------------------------------------------

def mark_snoozed(
    alarm_id: str,
) -> dict[str, Any]:

    return record_adherence(
        alarm_id=alarm_id,
        outcome=STATUS_SNOOZED,
        action_source="user",
    )


# ---------------------------------------------------------------------------
# Automatically detect missed alarms
# ---------------------------------------------------------------------------

def detect_missed_alarms() -> list[
    dict[str, Any]
]:
    """
    Mark old uncompleted alarms as missed.

    Rule:
        If an alarm is older than 30 minutes and still has a
        pending/due/ringing status, record it as missed.

    This is a project rule, not a medical rule.
    """

    alarms = load_alarms()

    records = load_adherence_records()

    now = _now()

    updated_records = []

    existing_alarm_ids = {
        record.get(
            "alarm_id"
        )
        for record in records
    }

    for alarm in alarms:

        alarm_id = alarm.get(
            "alarm_id"
        )

        if not alarm_id:
            continue

        if alarm_id in existing_alarm_ids:
            continue

        status = alarm.get(
            "status"
        )

        if status not in {
            "pending",
            "due",
            "ringing",
        }:
            continue

        scheduled_at = alarm.get(
            "scheduled_at"
        )

        if not scheduled_at:
            continue

        try:

            scheduled_time = (
                datetime.fromisoformat(
                    scheduled_at
                )
            )

        except ValueError:

            continue

        age_minutes = (
            now - scheduled_time
        ).total_seconds() / 60

        if age_minutes < 30:
            continue

        record = _create_record(
            alarm=alarm,
            outcome=STATUS_MISSED,
            action_source="system",
        )

        records.append(
            record
        )

        existing_alarm_ids.add(
            alarm_id
        )

        updated_records.append(
            record
        )

    save_adherence_records(
        records
    )

    return updated_records


# ---------------------------------------------------------------------------
# Today's history
# ---------------------------------------------------------------------------

def get_today_adherence() -> list[
    dict[str, Any]
]:
    """
    Return today's adherence records.
    """

    today = _now().date().isoformat()

    records = (
        load_adherence_records()
    )

    result = [
        record
        for record in records
        if record.get(
            "alarm_date"
        ) == today
    ]

    result.sort(
        key=lambda item: (
            item.get(
                "alarm_time"
            )
            or ""
        )
    )

    return result


# ---------------------------------------------------------------------------
# Full medication history
# ---------------------------------------------------------------------------

def get_medication_history(
    medicine_name: str | None = None,
) -> list[dict[str, Any]]:
    """
    Return medication adherence history.

    Optional:
        medicine_name
    """

    records = (
        load_adherence_records()
    )

    if not medicine_name:
        return records

    target = (
        str(
            medicine_name
        )
        .strip()
        .lower()
    )

    return [
        record
        for record in records
        if str(
            record.get(
                "medicine_name",
                "",
            )
        ).strip().lower()
        == target
    ]


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def get_adherence_summary(
    medicine_name: str | None = None,
) -> dict[str, Any]:
    """
    Calculate basic adherence counts.
    """

    records = get_medication_history(
        medicine_name
    )

    taken = sum(
        1
        for record in records
        if record.get(
            "outcome"
        ) == STATUS_TAKEN
    )

    missed = sum(
        1
        for record in records
        if record.get(
            "outcome"
        ) == STATUS_MISSED
    )

    skipped = sum(
        1
        for record in records
        if record.get(
            "outcome"
        ) == STATUS_SKIPPED
    )

    snoozed = sum(
        1
        for record in records
        if record.get(
            "outcome"
        ) == STATUS_SNOOZED
    )

    total = (
        taken
        + missed
        + skipped
    )

    adherence_rate = None

    if total > 0:

        adherence_rate = round(
            (
                taken / total
            ) * 100,
            1,
        )

    return {
        "medicine_name": medicine_name,

        "total_recorded": total,

        "taken": taken,

        "missed": missed,

        "skipped": skipped,

        "snoozed": snoozed,

        "adherence_rate_percent": (
            adherence_rate
        ),
    }


# ---------------------------------------------------------------------------
# Dashboard view
# ---------------------------------------------------------------------------

def build_today_dashboard() -> dict[
    str,
    Any,
]:
    """
    Build a frontend-friendly medication dashboard.
    """

    detect_missed_alarms()

    records = get_today_adherence()

    taken = [
        record
        for record in records
        if record.get(
            "outcome"
        ) == STATUS_TAKEN
    ]

    missed = [
        record
        for record in records
        if record.get(
            "outcome"
        ) == STATUS_MISSED
    ]

    skipped = [
        record
        for record in records
        if record.get(
            "outcome"
        ) == STATUS_SKIPPED
    ]

    return {
        "date": _now()
        .date()
        .isoformat(),

        "records": records,

        "counts": {
            "taken": len(taken),
            "missed": len(missed),
            "skipped": len(skipped),
        },

        "total": len(records),
    }


# ---------------------------------------------------------------------------
# Direct test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("=" * 72)
    print(
        "MEDICATION ADHERENCE SERVICE TEST"
    )
    print("=" * 72)

    alarms = load_alarms()

    print()
    print(
        f"Loaded alarms: {len(alarms)}"
    )

    if not alarms:

        print()
        print(
            "No alarms available for testing."
        )

        print(
            "Create a medication schedule and "
            "generate an alarm first."
        )

    else:

        test_alarm = alarms[0]

        alarm_id = test_alarm.get(
            "alarm_id"
        )

        print()
        print(
            "Using alarm:"
        )

        print(
            json.dumps(
                test_alarm,
                indent=2,
                ensure_ascii=False,
            )
        )

        try:

            result = mark_taken(
                alarm_id
            )

            print()
            print(
                "TAKEN RECORD:"
            )

            print(
                json.dumps(
                    result,
                    indent=2,
                    ensure_ascii=False,
                )
            )

        except Exception as exc:

            print()
            print(
                "TEST ERROR:"
            )

            print(
                str(exc)
            )

    print()
    print(
        "TODAY DASHBOARD:"
    )

    print(
        json.dumps(
            build_today_dashboard(),
            indent=2,
            ensure_ascii=False,
        )
    )

    print()
    print(
        "ADHERENCE SUMMARY:"
    )

    print(
        json.dumps(
            get_adherence_summary(),
            indent=2,
            ensure_ascii=False,
        )
    )

    print()
    print("=" * 72)
    print(
        "TEST COMPLETED"
    )
    print("=" * 72)