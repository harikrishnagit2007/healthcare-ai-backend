"""
medication_alarm_service.py

Purpose:
    Manage medication alarm instances from saved medication schedules.

Flow:

    medication_schedules.json
            ↓
    Generate alarm instances
            ↓
    Check current date/time
            ↓
    Alarm becomes DUE
            ↓
    RINGING state
            ↓
    TAKE / SNOOZE / SKIP
            ↓
    Alarm history

Important:
    - This module does NOT prescribe medication.
    - It does NOT decide when a medicine should be taken.
    - It only uses a schedule that has already been created and confirmed.
    - Actual phone-level full-screen alarm/ringtone will be connected later.
"""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

SCHEDULE_FILE = (
    BASE_DIR / "medication_schedules.json"
)

ALARM_FILE = (
    BASE_DIR / "medication_alarms.json"
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALARM_PENDING = "pending"
ALARM_DUE = "due"
ALARM_RINGING = "ringing"
ALARM_TAKEN = "taken"
ALARM_SKIPPED = "skipped"
ALARM_SNOOZED = "snoozed"
ALARM_CANCELLED = "cancelled"


VALID_ALARM_STATES = {
    ALARM_PENDING,
    ALARM_DUE,
    ALARM_RINGING,
    ALARM_TAKEN,
    ALARM_SKIPPED,
    ALARM_SNOOZED,
    ALARM_CANCELLED,
}


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    """
    Current local timezone-aware datetime.
    """

    return datetime.now().astimezone()


def _now_iso() -> str:
    return _now().isoformat()


def _parse_date(
    value: str,
) -> date:

    return datetime.strptime(
        value,
        "%Y-%m-%d",
    ).date()


def _parse_time(
    value: str,
):

    return datetime.strptime(
        value,
        "%H:%M",
    ).time()


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def _load_json_list(
    file_path: Path,
) -> list[dict[str, Any]]:

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


def _save_json_list(
    file_path: Path,
    data: list[dict[str, Any]],
) -> None:

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


# ---------------------------------------------------------------------------
# Schedule loading
# ---------------------------------------------------------------------------

def load_medication_schedules() -> list[dict[str, Any]]:
    """
    Load medication schedules created by
    medication_schedule_service.py.
    """

    return _load_json_list(
        SCHEDULE_FILE
    )


# ---------------------------------------------------------------------------
# Alarm storage
# ---------------------------------------------------------------------------

def load_alarms() -> list[dict[str, Any]]:
    """
    Load persisted alarm instances.
    """

    return _load_json_list(
        ALARM_FILE
    )


def save_alarms(
    alarms: list[dict[str, Any]],
) -> None:

    _save_json_list(
        ALARM_FILE,
        alarms,
    )


# ---------------------------------------------------------------------------
# Alarm ID
# ---------------------------------------------------------------------------

def _create_alarm_id() -> str:

    return (
        "alarm_"
        + uuid.uuid4().hex[:12]
    )


# ---------------------------------------------------------------------------
# Schedule date logic
# ---------------------------------------------------------------------------

def _is_schedule_active_on_date(
    schedule: dict[str, Any],
    target_date: date,
) -> bool:
    """
    Check whether a medication schedule applies to a date.
    """

    if schedule.get(
        "status"
    ) != "active":

        return False

    if not schedule.get(
        "confirmed_by_user",
        False,
    ):

        return False

    start_date_text = (
        schedule.get(
            "start_date"
        )
    )

    if not start_date_text:
        return False

    try:

        start_date = _parse_date(
            start_date_text
        )

    except ValueError:
        return False

    if target_date < start_date:
        return False

    end_date_text = (
        schedule.get(
            "end_date"
        )
    )

    if end_date_text:

        try:

            end_date = _parse_date(
                end_date_text
            )

        except ValueError:

            return False

        if target_date > end_date:
            return False

    repeat_days = (
        schedule.get(
            "repeat_days"
        )
        or []
    )

    weekday_name = (
        target_date.strftime(
            "%A"
        ).lower()
    )

    return (
        weekday_name
        in repeat_days
    )


# ---------------------------------------------------------------------------
# Generate alarms for one date
# ---------------------------------------------------------------------------

def generate_alarms_for_date(
    target_date: date | None = None,
) -> list[dict[str, Any]]:
    """
    Generate alarm instances for one target date.

    Existing alarm IDs for the same schedule/date/time
    are not duplicated.
    """

    if target_date is None:
        target_date = _now().date()

    schedules = (
        load_medication_schedules()
    )

    alarms = load_alarms()

    generated: list[
        dict[str, Any]
    ] = []

    existing_keys = {
        (
            alarm.get("schedule_id"),
            alarm.get("alarm_date"),
            alarm.get("alarm_time"),
        )
        for alarm in alarms
    }

    for schedule in schedules:

        if not _is_schedule_active_on_date(
            schedule,
            target_date,
        ):
            continue

        schedule_id = schedule.get(
            "schedule_id"
        )

        medicine_name = schedule.get(
            "medicine_name",
            "Medicine",
        )

        rxcui = schedule.get(
            "rxcui"
        )

        entries = (
            schedule.get(
                "schedule_entries"
            )
            or []
        )

        for entry in entries:

            period = (
                entry.get(
                    "period",
                    "",
                )
            )

            alarm_time = (
                entry.get(
                    "time",
                    "",
                )
            )

            if not alarm_time:
                continue

            unique_key = (
                schedule_id,
                target_date.isoformat(),
                alarm_time,
            )

            if unique_key in existing_keys:
                continue

            alarm_datetime = datetime.combine(
                target_date,
                _parse_time(
                    alarm_time
                ),
            ).astimezone()

            alarm = {
                "alarm_id": _create_alarm_id(),

                "schedule_id": schedule_id,

                "medicine_name": medicine_name,

                "rxcui": rxcui,

                "period": period,

                "alarm_date": (
                    target_date.isoformat()
                ),

                "alarm_time": alarm_time,

                "scheduled_at": (
                    alarm_datetime.isoformat()
                ),

                "status": ALARM_PENDING,

                "created_at": _now_iso(),

                "updated_at": _now_iso(),

                "snooze_count": 0,

                "snoozed_until": None,

                "actioned_at": None,

                "action": None,
            }

            alarms.append(
                alarm
            )

            generated.append(
                alarm
            )

            existing_keys.add(
                unique_key
            )

    save_alarms(
        alarms
    )

    return generated


# ---------------------------------------------------------------------------
# Generate alarms for date range
# ---------------------------------------------------------------------------

def generate_alarms_for_range(
    start_date: date,
    days: int = 7,
) -> list[dict[str, Any]]:
    """
    Generate future alarm instances.

    Default:
        7 days.
    """

    if days < 1:
        raise ValueError(
            "days must be at least 1."
        )

    if days > 31:
        raise ValueError(
            "days cannot exceed 31."
        )

    generated = []

    current_date = start_date

    for _ in range(days):

        daily = generate_alarms_for_date(
            current_date
        )

        generated.extend(
            daily
        )

        current_date += timedelta(
            days=1
        )

    return generated


# ---------------------------------------------------------------------------
# Refresh alarm states
# ---------------------------------------------------------------------------

def refresh_alarm_states() -> list[dict[str, Any]]:
    """
    Move pending alarms to DUE when their scheduled time arrives.

    Snoozed alarms become DUE again when snooze expires.
    """

    alarms = load_alarms()

    current_time = _now()

    changed = False

    for alarm in alarms:

        status = alarm.get(
            "status"
        )

        if status not in {
            ALARM_PENDING,
            ALARM_SNOOZED,
        }:
            continue

        # -------------------------------------------------------
        # Snoozed alarm
        # -------------------------------------------------------

        if status == ALARM_SNOOZED:

            snoozed_until_text = (
                alarm.get(
                    "snoozed_until"
                )
            )

            if not snoozed_until_text:
                continue

            try:

                snoozed_until = datetime.fromisoformat(
                    snoozed_until_text
                )

            except ValueError:
                continue

            if current_time >= snoozed_until:

                alarm[
                    "status"
                ] = ALARM_DUE

                alarm[
                    "updated_at"
                ] = _now_iso()

                changed = True

            continue

        # -------------------------------------------------------
        # Pending alarm
        # -------------------------------------------------------

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

        if current_time >= scheduled_time:

            alarm[
                "status"
            ] = ALARM_DUE

            alarm[
                "updated_at"
            ] = _now_iso()

            changed = True

    if changed:

        save_alarms(
            alarms
        )

    return alarms


# ---------------------------------------------------------------------------
# Get due alarms
# ---------------------------------------------------------------------------

def get_due_alarms() -> list[dict[str, Any]]:
    """
    Return alarms that currently need attention.
    """

    refresh_alarm_states()

    alarms = load_alarms()

    return [
        alarm
        for alarm in alarms
        if alarm.get(
            "status"
        )
        in {
            ALARM_DUE,
            ALARM_RINGING,
        }
    ]


# ---------------------------------------------------------------------------
# Start ringing
# ---------------------------------------------------------------------------

def start_alarm(
    alarm_id: str,
) -> dict[str, Any]:
    """
    Change a due alarm to RINGING.

    The frontend/native Android layer will later use this
    state to start the actual alarm interface and ringtone.
    """

    alarms = load_alarms()

    for alarm in alarms:

        if alarm.get(
            "alarm_id"
        ) != alarm_id:

            continue

        if alarm.get(
            "status"
        ) not in {
            ALARM_DUE,
            ALARM_RINGING,
        }:

            raise ValueError(
                "Only a due alarm can be started."
            )

        alarm[
            "status"
        ] = ALARM_RINGING

        alarm[
            "updated_at"
        ] = _now_iso()

        save_alarms(
            alarms
        )

        return alarm

    raise ValueError(
        f"Alarm not found: {alarm_id}"
    )


# ---------------------------------------------------------------------------
# Mark taken
# ---------------------------------------------------------------------------

def mark_alarm_taken(
    alarm_id: str,
) -> dict[str, Any]:
    """
    Mark medicine alarm as TAKEN.
    """

    return _complete_alarm(
        alarm_id=alarm_id,
        status=ALARM_TAKEN,
        action="taken",
    )


# ---------------------------------------------------------------------------
# Mark skipped
# ---------------------------------------------------------------------------

def mark_alarm_skipped(
    alarm_id: str,
) -> dict[str, Any]:
    """
    Mark medicine alarm as SKIPPED.

    This records the user action.
    It does not recommend skipping medication.
    """

    return _complete_alarm(
        alarm_id=alarm_id,
        status=ALARM_SKIPPED,
        action="skipped",
    )


def _complete_alarm(
    alarm_id: str,
    status: str,
    action: str,
) -> dict[str, Any]:

    if status not in {
        ALARM_TAKEN,
        ALARM_SKIPPED,
    }:

        raise ValueError(
            "Invalid completion state."
        )

    alarms = load_alarms()

    for alarm in alarms:

        if alarm.get(
            "alarm_id"
        ) != alarm_id:

            continue

        if alarm.get(
            "status"
        ) not in {
            ALARM_DUE,
            ALARM_RINGING,
            ALARM_SNOOZED,
        }:

            raise ValueError(
                "This alarm is not awaiting a user action."
            )

        alarm[
            "status"
        ] = status

        alarm[
            "action"
        ] = action

        alarm[
            "actioned_at"
        ] = _now_iso()

        alarm[
            "updated_at"
        ] = _now_iso()

        alarm[
            "snoozed_until"
        ] = None

        save_alarms(
            alarms
        )

        return alarm

    raise ValueError(
        f"Alarm not found: {alarm_id}"
    )


# ---------------------------------------------------------------------------
# Snooze
# ---------------------------------------------------------------------------

def snooze_alarm(
    alarm_id: str,
    minutes: int = 10,
) -> dict[str, Any]:
    """
    Snooze the alarm.

    Default:
        10 minutes.
    """

    try:
        minutes = int(minutes)

    except (TypeError, ValueError) as exc:

        raise ValueError(
            "Snooze minutes must be an integer."
        ) from exc

    if minutes < 1:

        raise ValueError(
            "Snooze duration must be at least 1 minute."
        )

    if minutes > 120:

        raise ValueError(
            "Snooze duration cannot exceed 120 minutes."
        )

    alarms = load_alarms()

    for alarm in alarms:

        if alarm.get(
            "alarm_id"
        ) != alarm_id:

            continue

        if alarm.get(
            "status"
        ) not in {
            ALARM_DUE,
            ALARM_RINGING,
        }:

            raise ValueError(
                "Only a due/ringing alarm can be snoozed."
            )

        snoozed_until = (
            _now()
            + timedelta(
                minutes=minutes
            )
        )

        alarm[
            "status"
        ] = ALARM_SNOOZED

        alarm[
            "snooze_count"
        ] = int(
            alarm.get(
                "snooze_count",
                0,
            )
        ) + 1

        alarm[
            "snoozed_until"
        ] = snoozed_until.isoformat()

        alarm[
            "action"
        ] = "snoozed"

        alarm[
            "updated_at"
        ] = _now_iso()

        save_alarms(
            alarms
        )

        return alarm

    raise ValueError(
        f"Alarm not found: {alarm_id}"
    )


# ---------------------------------------------------------------------------
# Today's alarms
# ---------------------------------------------------------------------------

def get_today_alarms() -> list[dict[str, Any]]:
    """
    Return today's alarm records.
    """

    today = _now().date().isoformat()

    # Ensure today's schedule has generated alarm instances.
    generate_alarms_for_date(
        _now().date()
    )

    alarms = load_alarms()

    result = [
        alarm
        for alarm in alarms
        if alarm.get(
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
# Alarm summary
# ---------------------------------------------------------------------------

def build_alarm_summary(
    alarm: dict[str, Any],
) -> dict[str, Any]:

    return {
        "alarm_id": alarm.get(
            "alarm_id"
        ),

        "medicine_name": alarm.get(
            "medicine_name"
        ),

        "date": alarm.get(
            "alarm_date"
        ),

        "time": alarm.get(
            "alarm_time"
        ),

        "period": alarm.get(
            "period"
        ),

        "status": alarm.get(
            "status"
        ),

        "snooze_count": alarm.get(
            "snooze_count",
            0,
        ),

        "scheduled_at": alarm.get(
            "scheduled_at"
        ),
    }


# ---------------------------------------------------------------------------
# Direct test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("=" * 72)
    print(
        "MEDICATION ALARM SERVICE TEST"
    )
    print("=" * 72)

    print()
    print(
        "1. Loading medication schedules..."
    )

    schedules = load_medication_schedules()

    print(
        f"Found {len(schedules)} schedule(s)."
    )

    print()
    print(
        "2. Generating today's alarms..."
    )

    today = _now().date()

    generated = generate_alarms_for_date(
        today
    )

    print(
        f"Generated {len(generated)} new alarm(s)."
    )

    print()
    print(
        "3. Today's alarms:"
    )

    today_alarms = get_today_alarms()

    if not today_alarms:

        print(
            "No alarms scheduled for today."
        )

    else:

        for alarm in today_alarms:

            summary = (
                build_alarm_summary(
                    alarm
                )
            )

            print()
            print(
                json.dumps(
                    summary,
                    indent=2,
                    ensure_ascii=False,
                )
            )

    print()
    print(
        "4. Current due alarms:"
    )

    due = get_due_alarms()

    if not due:

        print(
            "No alarms are currently due."
        )

    else:

        for alarm in due:

            print()
            print(
                json.dumps(
                    build_alarm_summary(
                        alarm
                    ),
                    indent=2,
                    ensure_ascii=False,
                )
            )

    print()
    print(
        "=" * 72
    )

    print(
        "TEST COMPLETED"
    )

    print(
        "=" * 72
    )