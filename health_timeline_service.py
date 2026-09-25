import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


BASE_DIR = Path(__file__).resolve().parent
TIMELINE_FILE = BASE_DIR / "health_timeline.json"


def _now_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _load_timeline() -> list[dict[str, Any]]:
    """Load timeline events from disk."""
    if not TIMELINE_FILE.exists():
        return []

    try:
        with TIMELINE_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except (OSError, json.JSONDecodeError):
        return []


def _save_timeline(events: list[dict[str, Any]]) -> None:
    """Save timeline events to disk."""
    temp_file = TIMELINE_FILE.with_suffix(".tmp")

    with temp_file.open("w", encoding="utf-8") as file:
        json.dump(events, file, indent=2, ensure_ascii=False)

    temp_file.replace(TIMELINE_FILE)


def add_timeline_event(
    event_type: str,
    title: str,
    details: Optional[str] = None,
    source: str = "system",
    event_date: Optional[str] = None,
    severity: str = "info",
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Add one event to the personal health timeline.

    This stores health-related information and does not make a diagnosis.
    """

    event_type = str(event_type).strip()
    title = str(title).strip()

    if not event_type:
        raise ValueError("event_type is required.")

    if not title:
        raise ValueError("title is required.")

    allowed_severity = {"info", "notice", "warning", "urgent"}

    if severity not in allowed_severity:
        raise ValueError(
            f"severity must be one of: {', '.join(sorted(allowed_severity))}"
        )

    event = {
        "event_id": f"timeline_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "timestamp": _now_iso(),
        "event_date": event_date or datetime.now().date().isoformat(),
        "event_type": event_type,
        "title": title,
        "details": details or "",
        "source": source,
        "severity": severity,
        "metadata": metadata or {},
    }

    events = _load_timeline()
    events.append(event)

    # Keep newest events first.
    events.sort(
        key=lambda item: item.get("timestamp", ""),
        reverse=True,
    )

    _save_timeline(events)

    return event


def get_timeline(
    limit: int = 100,
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Return timeline events with optional filtering."""

    if limit <= 0:
        raise ValueError("limit must be greater than 0.")

    events = _load_timeline()

    filtered: list[dict[str, Any]] = []

    for event in events:
        if event_type:
            if event.get("event_type") != event_type:
                continue

        event_date = event.get("event_date", "")

        if start_date and event_date < start_date:
            continue

        if end_date and event_date > end_date:
            continue

        filtered.append(event)

    return filtered[:limit]


def get_timeline_event(event_id: str) -> Optional[dict[str, Any]]:
    """Find one timeline event by ID."""

    for event in _load_timeline():
        if event.get("event_id") == event_id:
            return event

    return None


def delete_timeline_event(event_id: str) -> bool:
    """Delete one timeline event by ID."""

    events = _load_timeline()

    remaining = [
        event
        for event in events
        if event.get("event_id") != event_id
    ]

    if len(remaining) == len(events):
        return False

    _save_timeline(remaining)
    return True


def get_timeline_summary() -> dict[str, Any]:
    """Return a simple summary of the stored timeline."""

    events = _load_timeline()

    type_counts: dict[str, int] = {}

    for event in events:
        event_type = event.get("event_type", "unknown")
        type_counts[event_type] = type_counts.get(event_type, 0) + 1

    latest_event = events[0] if events else None

    return {
        "total_events": len(events),
        "event_types": type_counts,
        "latest_event": latest_event,
    }


def record_symptom_event(
    symptom_name: str,
    status: str,
    details: str = "",
) -> dict[str, Any]:
    """Record a symptom-related timeline event."""

    return add_timeline_event(
        event_type="symptom",
        title=f"Symptom: {symptom_name}",
        details=details or f"Symptom status: {status}",
        source="symptom_service",
        severity="notice",
        metadata={
            "symptom": symptom_name,
            "status": status,
        },
    )


def record_medication_event(
    medicine_name: str,
    action: str,
    details: str = "",
) -> dict[str, Any]:
    """Record a medication-related timeline event."""

    return add_timeline_event(
        event_type="medication",
        title=f"Medication: {medicine_name}",
        details=details or f"Medication action: {action}",
        source="medication_service",
        severity="info",
        metadata={
            "medicine_name": medicine_name,
            "action": action,
        },
    )


def record_adherence_event(
    medicine_name: str,
    status: str,
    scheduled_time: str = "",
) -> dict[str, Any]:
    """Record medication adherence."""

    return add_timeline_event(
        event_type="adherence",
        title=f"Medication {status}: {medicine_name}",
        details=(
            f"Scheduled time: {scheduled_time}"
            if scheduled_time
            else ""
        ),
        source="medication_adherence_service",
        severity="info" if status == "taken" else "notice",
        metadata={
            "medicine_name": medicine_name,
            "status": status,
            "scheduled_time": scheduled_time,
        },
    )


def record_care_event(
    care_type: str,
    name: str,
    address: str = "",
) -> dict[str, Any]:
    """Record a care-navigation event."""

    return add_timeline_event(
        event_type="care_navigation",
        title=f"{care_type}: {name}",
        details=address,
        source="care_location_service",
        severity="info",
        metadata={
            "care_type": care_type,
            "name": name,
            "address": address,
        },
    )


def clear_timeline() -> None:
    """Delete all timeline events."""
    _save_timeline([])


def run_local_test() -> None:
    print("\nHEALTH TIMELINE SERVICE TEST")
    print("=" * 40)

    print("\n1. Loading timeline...")
    events = get_timeline()
    print(f"Existing events: {len(events)}")

    print("\n2. Adding test event...")

    test_event = add_timeline_event(
        event_type="system_test",
        title="Healthcare AI timeline test",
        details="Timeline service is working correctly.",
        source="local_test",
        severity="info",
    )

    print("Created event:")
    print(json.dumps(test_event, indent=2, ensure_ascii=False))

    print("\n3. Reading timeline...")
    timeline = get_timeline()
    print(f"Total events: {len(timeline)}")

    print("\n4. Timeline summary...")
    summary = get_timeline_summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    print("\n5. Latest event...")
    if timeline:
        print(json.dumps(timeline[0], indent=2, ensure_ascii=False))
    else:
        print("No events found.")

    print("\nTimeline service test completed.")


if __name__ == "__main__":
    run_local_test()