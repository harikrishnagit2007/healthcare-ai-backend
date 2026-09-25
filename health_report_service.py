import json
from datetime import datetime, date
from pathlib import Path
from typing import Any, Optional


BASE_DIR = Path(__file__).resolve().parent

TIMELINE_FILE = BASE_DIR / "health_timeline.json"
SCHEDULE_FILE = BASE_DIR / "medication_schedules.json"
ADHERENCE_FILE = BASE_DIR / "medication_adherence.json"
CONFIRMATION_FILE = BASE_DIR / "symptom_confirmations.json"


def load_json_file(path: Path, default: Any) -> Any:
    """Safely load a JSON file."""

    if not path.exists():
        return default

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return default


def normalize_list(data: Any) -> list:
    """Convert common container formats into a list."""

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in (
            "items",
            "events",
            "schedules",
            "records",
            "confirmations",
            "symptoms",
        ):
            value = data.get(key)

            if isinstance(value, list):
                return value

    return []


def load_timeline() -> list[dict[str, Any]]:
    data = load_json_file(TIMELINE_FILE, [])
    return normalize_list(data)


def load_schedules() -> list[dict[str, Any]]:
    data = load_json_file(SCHEDULE_FILE, [])
    return normalize_list(data)


def load_adherence() -> list[dict[str, Any]]:
    data = load_json_file(ADHERENCE_FILE, [])

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ("records", "events", "adherence"):
            if isinstance(data.get(key), list):
                return data[key]

    return []


def load_confirmations() -> Any:
    return load_json_file(CONFIRMATION_FILE, {})


def get_confirmed_symptoms() -> list[str]:
    """Read currently confirmed symptoms."""

    data = load_confirmations()

    # Typical format:
    # {
    #   "dizziness": true,
    #   "headache": false
    # }

    if isinstance(data, dict):
        confirmed = []

        for symptom, value in data.items():
            if isinstance(value, dict):
                value = value.get("confirmed", value.get("status"))

            if value is True:
                confirmed.append(str(symptom))

            elif isinstance(value, str):
                if value.lower() in {
                    "true",
                    "yes",
                    "confirmed",
                    "current",
                }:
                    confirmed.append(str(symptom))

        return confirmed

    # Alternative format:
    # [{"symptom": "dizziness", "confirmed": true}]

    if isinstance(data, list):
        confirmed = []

        for item in data:
            if not isinstance(item, dict):
                continue

            symptom = (
                item.get("symptom")
                or item.get("symptom_name")
                or item.get("name")
            )

            confirmed_value = item.get(
                "confirmed",
                item.get("status"),
            )

            if not symptom:
                continue

            if confirmed_value is True:
                confirmed.append(str(symptom))

            elif isinstance(confirmed_value, str):
                if confirmed_value.lower() in {
                    "true",
                    "yes",
                    "confirmed",
                    "current",
                }:
                    confirmed.append(str(symptom))

        return confirmed

    return []


def get_active_schedules(
    schedules: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return schedules that appear to be active."""

    today = date.today().isoformat()
    active = []

    for schedule in schedules:

        if schedule.get("confirmed") is False:
            continue

        if schedule.get("paused") is True:
            continue

        start_date = schedule.get("start_date")
        end_date = schedule.get("end_date")

        if start_date and today < str(start_date):
            continue

        if end_date and today > str(end_date):
            continue

        active.append(schedule)

    return active


def calculate_adherence(
    records: list[dict[str, Any]],
) -> dict[str, int]:
    """Calculate simple adherence totals."""

    taken = 0
    missed = 0
    skipped = 0
    snoozed = 0

    today = date.today().isoformat()

    for record in records:
        record_date = (
            record.get("date")
            or record.get("event_date")
            or record.get("scheduled_date")
            or ""
        )

        if record_date and str(record_date) != today:
            continue

        status = str(
            record.get("status", "")
        ).lower()

        if status == "taken":
            taken += 1

        elif status == "missed":
            missed += 1

        elif status == "skipped":
            skipped += 1

        elif status == "snoozed":
            snoozed += 1

    total = taken + missed + skipped

    percentage: Optional[float] = None

    if total > 0:
        percentage = round((taken / total) * 100, 1)

    return {
        "taken": taken,
        "missed": missed,
        "skipped": skipped,
        "snoozed": snoozed,
        "total_tracked": total,
        "adherence_percentage": percentage,
    }


def get_recent_changes(
    timeline: list[dict[str, Any]],
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Return recent timeline events."""

    sorted_events = sorted(
        timeline,
        key=lambda event: (
            str(
                event.get("timestamp")
                or event.get("event_date")
                or ""
            )
        ),
        reverse=True,
    )

    return sorted_events[:limit]


def build_attention_items(
    symptoms: list[str],
    recent_events: list[dict[str, Any]],
    adherence: dict[str, Any],
) -> list[str]:
    """
    Build informational attention items.

    These are not diagnoses or medical determinations.
    """

    items = []

    if symptoms:
        items.append(
            f"{len(symptoms)} current symptom"
            f"{'s' if len(symptoms) != 1 else ''} "
            "has been confirmed by the user."
        )

    for event in recent_events[:2]:
        title = event.get("title")

        if title:
            items.append(
                f"Recent health event: {title}"
            )

    if adherence.get("missed", 0) > 0:
        items.append(
            f"{adherence['missed']} medication adherence "
            "event(s) are recorded as missed today."
        )

    if not items:
        items.append(
            "No new attention items are currently recorded."
        )

    return items


def build_doctor_context(
    symptoms: list[str],
    active_schedules: list[dict[str, Any]],
    recent_events: list[dict[str, Any]],
    adherence: dict[str, Any],
) -> dict[str, Any]:

    medicines = []

    for schedule in active_schedules:

        medicine_name = (
            schedule.get("medicine_name")
            or schedule.get("medicine")
            or schedule.get("name")
        )

        if medicine_name:
            medicines.append(str(medicine_name))

    return {
        "current_symptoms": symptoms,
        "active_medicines": sorted(set(medicines)),
        "recent_events": recent_events,
        "adherence": adherence,
        "note": (
            "This section organizes recorded information "
            "for healthcare professional review."
        ),
    }


def build_health_report() -> dict[str, Any]:
    """Build the complete AI Health Report Card."""

    timeline = load_timeline()
    schedules = load_schedules()
    adherence_records = load_adherence()

    symptoms = get_confirmed_symptoms()
    active_schedules = get_active_schedules(schedules)

    adherence = calculate_adherence(
        adherence_records
    )

    recent_events = get_recent_changes(
        timeline,
        limit=5,
    )

    attention_items = build_attention_items(
        symptoms=symptoms,
        recent_events=recent_events,
        adherence=adherence,
    )

    doctor_context = build_doctor_context(
        symptoms=symptoms,
        active_schedules=active_schedules,
        recent_events=recent_events,
        adherence=adherence,
    )

    return {
        "report_type": "AI Health Report Card",
        "generated_at": datetime.now().isoformat(),
        "report_date": date.today().isoformat(),

        "current_health": {
            "confirmed_symptoms": symptoms,
            "symptom_count": len(symptoms),
        },

        "recent_changes": recent_events,

        "medication": {
            "active_schedule_count": len(
                active_schedules
            ),
            "active_schedules": active_schedules,
        },

        "adherence": adherence,

        "what_matters_now": attention_items,

        "doctor_context": doctor_context,

        "safety_note": (
            "This report summarizes recorded health information "
            "and is not a confirmed diagnosis, prescription, "
            "or substitute for professional medical evaluation."
        ),
    }


def save_report(
    report: dict[str, Any],
    output_file: Optional[Path] = None,
) -> Path:

    if output_file is None:
        output_file = BASE_DIR / "latest_health_report.json"

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return output_file


def print_report(report: dict[str, Any]) -> None:

    print()
    print("=" * 60)
    print("AI HEALTH REPORT CARD")
    print("=" * 60)

    print()
    print("REPORT DATE:")
    print(report["report_date"])

    print()
    print("CURRENT SYMPTOMS:")

    symptoms = report["current_health"][
        "confirmed_symptoms"
    ]

    if symptoms:
        for symptom in symptoms:
            print(f"  • {symptom}")
    else:
        print("  No confirmed symptoms recorded.")

    print()
    print("MEDICATION:")

    medication = report["medication"]

    print(
        f"  Active schedules: "
        f"{medication['active_schedule_count']}"
    )

    for schedule in medication["active_schedules"]:

        name = (
            schedule.get("medicine_name")
            or schedule.get("medicine")
            or schedule.get("name")
            or "Unknown medicine"
        )

        times = []

        if schedule.get("morning"):
            times.append(
                f"Morning {schedule.get('morning_time', '')}"
            )

        if schedule.get("afternoon"):
            times.append(
                f"Afternoon "
                f"{schedule.get('afternoon_time', '')}"
            )

        if schedule.get("evening"):
            times.append(
                f"Evening {schedule.get('evening_time', '')}"
            )

        if schedule.get("night"):
            times.append(
                f"Night {schedule.get('night_time', '')}"
            )

        print(
            f"  • {name}"
            + (
                f" — {' · '.join(times)}"
                if times
                else ""
            )
        )

    print()
    print("ADHERENCE:")

    adherence = report["adherence"]

    print(
        f"  Taken: {adherence['taken']}"
    )

    print(
        f"  Missed: {adherence['missed']}"
    )

    print(
        f"  Skipped: {adherence['skipped']}"
    )

    print(
        f"  Snoozed: {adherence['snoozed']}"
    )

    if adherence["adherence_percentage"] is not None:
        print(
            f"  Adherence: "
            f"{adherence['adherence_percentage']}%"
        )

    print()
    print("WHAT MATTERS NOW:")

    for item in report["what_matters_now"]:
        print(f"  • {item}")

    print()
    print("RECENT EVENTS:")

    recent_events = report["recent_changes"]

    if recent_events:
        for event in recent_events:

            title = event.get(
                "title",
                "Health event",
            )

            event_date = event.get(
                "event_date",
                "",
            )

            print(
                f"  • {event_date} — {title}"
            )

    else:
        print("  No recent events recorded.")

    print()
    print("DOCTOR CONTEXT:")

    doctor_context = report["doctor_context"]

    print(
        "  Symptoms: "
        + (
            ", ".join(
                doctor_context["current_symptoms"]
            )
            if doctor_context["current_symptoms"]
            else "None recorded"
        )
    )

    print(
        "  Medicines: "
        + (
            ", ".join(
                doctor_context["active_medicines"]
            )
            if doctor_context["active_medicines"]
            else "None recorded"
        )
    )

    print()
    print("SAFETY NOTE:")
    print(
        f"  {report['safety_note']}"
    )

    print()
    print("=" * 60)


def run_local_test() -> None:

    print(
        "\nGenerating AI Health Report Card..."
    )

    report = build_health_report()

    output_file = save_report(report)

    print_report(report)

    print()
    print(
        f"Saved report to: {output_file}"
    )


if __name__ == "__main__":
    run_local_test()