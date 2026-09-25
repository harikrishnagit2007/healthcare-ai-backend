from __future__ import annotations

import re
from typing import Any


# ============================================================
# SAFETY GUARD
# ============================================================

EMERGENCY_PATTERNS = {
    "breathing_difficulty": [
        "difficulty breathing",
        "cannot breathe",
        "can't breathe",
        "shortness of breath",
        "severe breathing problem",
        "struggling to breathe",
    ],
    "chest_pain": [
        "severe chest pain",
        "chest pain",
        "pressure in chest",
        "tightness in chest",
    ],
    "severe_bleeding": [
        "severe bleeding",
        "heavy bleeding",
        "bleeding won't stop",
        "bleeding will not stop",
    ],
    "loss_of_consciousness": [
        "unconscious",
        "passed out",
        "loss of consciousness",
        "not responding",
    ],
    "seizure": [
        "seizure",
        "convulsion",
        "fits",
    ],
    "sudden_neurological_change": [
        "sudden weakness",
        "one sided weakness",
        "one-sided weakness",
        "face drooping",
        "difficulty speaking",
        "cannot speak",
        "sudden confusion",
        "sudden numbness",
    ],
    "severe_allergic_reaction": [
        "anaphylaxis",
        "severe allergic reaction",
        "swelling of throat",
        "throat swelling",
        "can't swallow",
        "cannot swallow",
    ],
}


URGENT_PATTERNS = {
    "high_fever": [
        "very high fever",
        "high fever",
    ],
    "persistent_vomiting": [
        "persistent vomiting",
        "vomiting continuously",
        "cannot keep fluids down",
    ],
    "severe_pain": [
        "unbearable pain",
        "extreme pain",
        "severe pain",
    ],
    "rapid_worsening": [
        "getting worse quickly",
        "rapidly getting worse",
        "suddenly getting worse",
        "condition is worsening",
    ],
}


def _normalize(text: str) -> str:
    text = str(text or "").lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _find_matches(
    text: str,
    patterns: dict[str, list[str]],
) -> list[dict[str, str]]:

    normalized = _normalize(text)
    matches: list[dict[str, str]] = []

    for category, phrases in patterns.items():
        for phrase in phrases:
            if phrase in normalized:
                matches.append(
                    {
                        "category": category,
                        "matched_phrase": phrase,
                    }
                )

    return matches


def analyze_safety(
    question: str = "",
    symptom_text: str = "",
) -> dict[str, Any]:
    """
    Analyze user-provided text for predefined safety signals.

    This is a safety-screening layer, not a diagnosis.
    """

    combined_text = (
        f"{question or ''} {symptom_text or ''}"
    ).strip()

    emergency_matches = _find_matches(
        combined_text,
        EMERGENCY_PATTERNS,
    )

    urgent_matches = _find_matches(
        combined_text,
        URGENT_PATTERNS,
    )

    if emergency_matches:
        level = "emergency"
        action = (
            "Seek urgent medical attention now. "
            "Contact local emergency services or go to "
            "the nearest emergency department."
        )

    elif urgent_matches:
        level = "urgent"
        action = (
            "Consider prompt medical evaluation, especially "
            "if symptoms are worsening, severe, or persistent."
        )

    else:
        level = "routine"
        action = (
            "No predefined emergency signal was detected "
            "from the information provided."
        )

    return {
        "level": level,
        "safe_to_continue": level != "emergency",
        "action": action,
        "emergency_signals": emergency_matches,
        "urgent_signals": urgent_matches,
        "disclaimer": (
            "This safety screen does not diagnose a medical "
            "condition and cannot rule out an emergency."
        ),
    }


def build_safety_message(
    safety_result: dict[str, Any],
) -> str:

    level = safety_result.get("level")

    if level == "emergency":
        return (
            "Safety alert: the information you provided "
            "contains a possible emergency warning sign. "
            "Please seek urgent medical attention now. "
            "This system cannot determine the cause."
        )

    if level == "urgent":
        return (
            "Attention: the information provided may deserve "
            "prompt medical evaluation. Please consider "
            "contacting a healthcare professional."
        )

    return (
        "No predefined emergency warning signal was detected "
        "from the information provided."
    )


def run_safety_guard(
    question: str = "",
    symptom_text: str = "",
) -> dict[str, Any]:

    result = analyze_safety(
        question=question,
        symptom_text=symptom_text,
    )

    result["user_message"] = build_safety_message(
        result
    )

    return result


def run_local_test() -> None:

    print()
    print("=" * 55)
    print("SAFETY GUARD SERVICE TEST")
    print("=" * 55)

    tests = [
        "I have a mild headache.",
        "I have chest pain and difficulty breathing.",
        "I have been vomiting continuously.",
    ]

    for index, text in enumerate(tests, start=1):

        print()
        print(f"TEST {index}")
        print(f"Input: {text}")

        result = run_safety_guard(
            question=text
        )

        print(f"Level: {result['level']}")
        print(f"Action: {result['action']}")
        print(
            f"Safe to continue: "
            f"{result['safe_to_continue']}"
        )

    print()
    print("Safety guard test completed.")


if __name__ == "__main__":
    run_local_test()