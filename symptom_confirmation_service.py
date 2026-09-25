"""
symptom_confirmation_service.py

Purpose:
    1. Compare previous and current symptom information.
    2. Detect possible symptom changes.
    3. Generate simple YES/NO confirmation questions.
    4. Store user confirmations.
    5. Keep symptom confirmation separate from diagnosis.

This module does NOT diagnose diseases.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONFIRMATION_FILE = Path(__file__).with_name("symptom_confirmations.json")


# ---------------------------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    """Return the current UTC time as an ISO timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _clean_text(value: Any) -> str:
    """Convert a value to clean lowercase text."""
    if value is None:
        return ""

    text = str(value).strip().lower()

    # Normalize common separators.
    text = text.replace("\n", ",")
    text = text.replace(";", ",")

    return text.strip()


def _normalize_symptom_name(symptom: str) -> str:
    """
    Normalize a symptom name.

    Examples:
        "Dizziness" -> "dizziness"
        " severe dizziness " -> "severe dizziness"
    """
    symptom = _clean_text(symptom)

    # Remove common leading bullet characters.
    symptom = symptom.lstrip("-•* ").strip()

    # Collapse repeated spaces.
    symptom = " ".join(symptom.split())

    return symptom


def _parse_symptom_text(text: str) -> list[str]:
    """
    Parse comma-separated or line-separated symptoms.
    """
    text = str(text or "").replace("\n", ",").replace(";", ",")

    symptoms: list[str] = []

    for item in text.split(","):
        item = _normalize_symptom_name(item)

        if item:
            symptoms.append(item)

    return symptoms


# ---------------------------------------------------------------------------
# Symptom status normalization
# ---------------------------------------------------------------------------

def _normalize_status_value(value: Any) -> str:
    """
    Normalize a status value.

    Returns one of:
        present
        absent
        unknown
    """

    if isinstance(value, bool):
        return "present" if value else "absent"

    text = _clean_text(value)

    present_values = {
        "yes",
        "true",
        "present",
        "positive",
        "having",
        "experienced",
        "experiencing",
        "1",
    }

    absent_values = {
        "no",
        "false",
        "absent",
        "negative",
        "none",
        "denied",
        "denies",
        "not",
        "0",
    }

    if text in present_values:
        return "present"

    if text in absent_values:
        return "absent"

    return "unknown"


def _normalize_symptom_data(data: Any) -> dict[str, str]:
    """
    Convert different symptom input formats into:

        {
            "dizziness": "present",
            "headache": "present",
            "fever": "absent"
        }

    Supported input forms:

    1. List:
        ["headache", "dizziness"]

    2. String:
        "headache, dizziness"

    3. Dictionary:
        {
            "dizziness": True,
            "headache": False
        }

    4. Dictionary with status strings:
        {
            "dizziness": "present",
            "headache": "absent"
        }
    """

    result: dict[str, str] = {}

    if data is None:
        return result

    # -------------------------------------------------------
    # Dictionary input
    # -------------------------------------------------------
    if isinstance(data, dict):
        for raw_name, raw_status in data.items():
            name = _normalize_symptom_name(str(raw_name))

            if not name:
                continue

            status = _normalize_status_value(raw_status)

            # Handle values such as:
            # {"dizziness": "no"}
            if status == "unknown":
                status = "present"

            result[name] = status

        return result

    # -------------------------------------------------------
    # List / tuple / set input
    # -------------------------------------------------------
    if isinstance(data, (list, tuple, set)):
        for raw_item in data:
            text = _normalize_symptom_name(str(raw_item))

            if not text:
                continue

            # Negative symptom forms:
            # "no dizziness"
            # "not dizziness"
            # "denies dizziness"
            # "without dizziness"
            negative_prefixes = (
                "no ",
                "not ",
                "denies ",
                "without ",
            )

            matched_negative = False

            for prefix in negative_prefixes:
                if text.startswith(prefix):
                    symptom_name = text[len(prefix):].strip()

                    if symptom_name:
                        result[symptom_name] = "absent"

                    matched_negative = True
                    break

            if matched_negative:
                continue

            result[text] = "present"

        return result

    # -------------------------------------------------------
    # String input
    # -------------------------------------------------------
    if isinstance(data, str):
        parts = _parse_symptom_text(data)

        for item in parts:
            negative_prefixes = (
                "no ",
                "not ",
                "denies ",
                "without ",
            )

            handled = False

            for prefix in negative_prefixes:
                if item.startswith(prefix):
                    symptom_name = item[len(prefix):].strip()

                    if symptom_name:
                        result[symptom_name] = "absent"

                    handled = True
                    break

            if handled:
                continue

            result[item] = "present"

        return result

    # -------------------------------------------------------
    # Fallback
    # -------------------------------------------------------
    text = _normalize_symptom_name(str(data))

    if text:
        result[text] = "present"

    return result


# ---------------------------------------------------------------------------
# Symptom comparison
# ---------------------------------------------------------------------------

def compare_symptoms(
    previous_symptoms: Any,
    current_symptoms: Any,
) -> dict[str, Any]:
    """
    Compare previous and current symptom information.

    Returns:

    {
        "previous": {...},
        "current": {...},
        "new_symptoms": [...],
        "removed_symptoms": [...],
        "changed_symptoms": [...]
    }

    Important:
        This function detects information changes only.
        It does not diagnose a disease.
    """

    previous = _normalize_symptom_data(previous_symptoms)
    current = _normalize_symptom_data(current_symptoms)

    previous_names = set(previous.keys())
    current_names = set(current.keys())

    new_symptoms: list[str] = []
    removed_symptoms: list[str] = []
    changed_symptoms: list[dict[str, str]] = []

    # -------------------------------------------------------
    # Symptoms appearing for the first time
    # -------------------------------------------------------
    for symptom in sorted(current_names - previous_names):
        if current[symptom] == "present":
            new_symptoms.append(symptom)

    # -------------------------------------------------------
    # Symptoms no longer present / explicitly absent
    # -------------------------------------------------------
    for symptom in sorted(previous_names - current_names):
        if previous[symptom] == "present":
            removed_symptoms.append(symptom)

    # -------------------------------------------------------
    # Same symptom with a changed status
    # -------------------------------------------------------
    for symptom in sorted(previous_names & current_names):
        old_status = previous[symptom]
        new_status = current[symptom]

        if old_status != new_status:
            changed_symptoms.append(
                {
                    "symptom": symptom,
                    "previous_status": old_status,
                    "current_status": new_status,
                }
            )

            # Negative -> Positive can also be treated as a
            # candidate "new symptom" for confirmation.
            if old_status == "absent" and new_status == "present":
                if symptom not in new_symptoms:
                    new_symptoms.append(symptom)

    return {
        "previous": previous,
        "current": current,
        "new_symptoms": sorted(set(new_symptoms)),
        "removed_symptoms": sorted(set(removed_symptoms)),
        "changed_symptoms": changed_symptoms,
    }


# ---------------------------------------------------------------------------
# Candidate symptom extraction
# ---------------------------------------------------------------------------

def extract_symptom_changes(
    previous_symptoms: Any,
    current_symptoms: Any,
) -> dict[str, Any]:
    """
    Alias/helper for the agent layer.

    Returns the symptom-change analysis.
    """
    return compare_symptoms(
        previous_symptoms=previous_symptoms,
        current_symptoms=current_symptoms,
    )


def get_candidate_symptoms(
    comparison_result: dict[str, Any],
) -> list[str]:
    """
    Get symptoms that should be confirmed with the user.

    Candidate symptoms come from:
        - new symptoms
        - absent -> present changes
    """

    candidates = set()

    for symptom in comparison_result.get("new_symptoms", []):
        candidates.add(symptom)

    for change in comparison_result.get("changed_symptoms", []):
        if (
            change.get("previous_status") == "absent"
            and change.get("current_status") == "present"
        ):
            symptom = change.get("symptom", "").strip()

            if symptom:
                candidates.add(symptom)

    return sorted(candidates)


# ---------------------------------------------------------------------------
# Confirmation question generation
# ---------------------------------------------------------------------------

def create_confirmation_question(symptom: str) -> dict[str, Any]:
    """
    Create a single YES/NO confirmation question.
    """

    symptom = _normalize_symptom_name(symptom)

    return {
        "question": f"Are you currently experiencing {symptom}?",
        "type": "yes_no",
        "candidate": symptom,
    }


def create_confirmation_questions(
    comparison_result: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Convert possible symptom changes into confirmation questions.
    """

    candidates = get_candidate_symptoms(comparison_result)

    questions = []

    for symptom in candidates:
        questions.append(
            create_confirmation_question(symptom)
        )

    return questions


# ---------------------------------------------------------------------------
# Confirmation storage
# ---------------------------------------------------------------------------

def load_confirmations() -> list[dict[str, Any]]:
    """
    Load stored confirmation records.
    """

    if not CONFIRMATION_FILE.exists():
        return []

    try:
        with CONFIRMATION_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except (json.JSONDecodeError, OSError):
        return []


def save_confirmations(
    confirmations: list[dict[str, Any]],
) -> None:
    """
    Save confirmation records to JSON.
    """

    with CONFIRMATION_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            confirmations,
            file,
            indent=2,
            ensure_ascii=False,
        )


def record_confirmation(
    candidate: str,
    confirmed: bool,
) -> dict[str, Any]:
    """
    Store a YES/NO confirmation.

    Example:

        {
            "candidate": "dizziness",
            "confirmed": true,
            "timestamp": "..."
        }
    """

    candidate = _normalize_symptom_name(candidate)

    if not candidate:
        raise ValueError("Symptom candidate cannot be empty.")

    record = {
        "candidate": candidate,
        "confirmed": bool(confirmed),
        "timestamp": _utc_now(),
    }

    confirmations = load_confirmations()

    # Update an existing record for the same candidate.
    updated = False

    for existing in confirmations:
        if existing.get("candidate") == candidate:
            existing.update(record)
            updated = True
            break

    if not updated:
        confirmations.append(record)

    save_confirmations(confirmations)

    return record


# ---------------------------------------------------------------------------
# Read confirmed symptoms
# ---------------------------------------------------------------------------

def get_confirmed_symptoms() -> list[str]:
    """
    Return all symptoms that the user explicitly confirmed.
    """

    confirmations = load_confirmations()

    confirmed = {
        item.get("candidate")
        for item in confirmations
        if item.get("confirmed") is True
        and item.get("candidate")
    }

    return sorted(confirmed)


def get_rejected_symptoms() -> list[str]:
    """
    Return all symptom candidates explicitly rejected by the user.
    """

    confirmations = load_confirmations()

    rejected = {
        item.get("candidate")
        for item in confirmations
        if item.get("confirmed") is False
        and item.get("candidate")
    }

    return sorted(rejected)


# ---------------------------------------------------------------------------
# Complete analysis helper
# ---------------------------------------------------------------------------

def analyze_symptom_confirmation(
    previous_symptoms: Any,
    current_symptoms: Any,
) -> dict[str, Any]:
    """
    Run the full symptom-confirmation preparation pipeline.

    This function:
        1. compares symptoms
        2. extracts candidate changes
        3. creates YES/NO questions

    It does NOT automatically confirm anything.
    """

    comparison = compare_symptoms(
        previous_symptoms=previous_symptoms,
        current_symptoms=current_symptoms,
    )

    questions = create_confirmation_questions(comparison)

    return {
        "comparison": comparison,
        "candidate_symptoms": get_candidate_symptoms(comparison),
        "questions": questions,
        "requires_confirmation": len(questions) > 0,
        "confirmed_symptoms": get_confirmed_symptoms(),
        "rejected_symptoms": get_rejected_symptoms(),
    }


# ---------------------------------------------------------------------------
# Simple interactive test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("SYMPTOM CONFIRMATION SERVICE TEST")
    print("=" * 70)

    previous = [
        "headache",
        "no dizziness",
        "fatigue",
    ]

    current = [
        "headache",
        "dizziness",
        "fatigue",
    ]

    print("\nPREVIOUS SYMPTOMS:")
    print(previous)

    print("\nCURRENT SYMPTOMS:")
    print(current)

    result = analyze_symptom_confirmation(
        previous_symptoms=previous,
        current_symptoms=current,
    )

    print("\nCOMPARISON:")
    print(
        json.dumps(
            result["comparison"],
            indent=2,
            ensure_ascii=False,
        )
    )

    print("\nCANDIDATE SYMPTOMS:")
    print(result["candidate_symptoms"])

    print("\nCONFIRMATION QUESTIONS:")

    for question in result["questions"]:
        print(
            f'- {question["question"]}'
        )

    # Simulate user saying YES.
    if result["questions"]:
        first_candidate = result["questions"][0]["candidate"]

        confirmation = record_confirmation(
            candidate=first_candidate,
            confirmed=True,
        )

        print("\nSIMULATED USER CONFIRMATION:")
        print(
            json.dumps(
                confirmation,
                indent=2,
                ensure_ascii=False,
            )
        )

    print("\nCONFIRMED SYMPTOMS:")
    print(get_confirmed_symptoms())

    print("\nREJECTED SYMPTOMS:")
    print(get_rejected_symptoms())

    print("\n" + "=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)