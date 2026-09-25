import json
import os

VERIFIED_FILE = "verified_medications.json"


def verify_medication(candidate, confirmed=False):

    required_fields = [
        "medicine_name",
        "dosage",
        "frequency",
        "duration"
    ]

    for field in required_fields:
        if field not in candidate:
            candidate[field] = "Not detected"

    if not confirmed:

        return {
            "status": "verification_required",
            "medicine": candidate,
            "message": "Review the extracted information against the original prescription before confirming."
        }

    if candidate["medicine_name"] == "Not detected":

        return {
            "status": "verification_failed",
            "medicine": candidate,
            "message": "Medicine name was not detected."
        }

    existing = []

    if os.path.exists(VERIFIED_FILE):

        with open(
            VERIFIED_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            existing = json.load(file)

    existing.append(candidate)

    with open(
        VERIFIED_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            existing,
            file,
            indent=4
        )

    return {
        "status": "verified",
        "medicine": candidate,
        "message": "Medication information saved after confirmation."
    }