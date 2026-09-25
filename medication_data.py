import json

MEDICATION_FILE = "medication_record.json"


def get_medication_data():
    with open(
        MEDICATION_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        medication = json.load(file)

    return {
        "medications": [
            medication
        ],
        "prescription": {
            "doctor_name": "Not provided",
            "visit_date": medication.get(
                "start_date",
                "Not provided"
            ),
            "notes": "Imported from saved prescription record"
        }
    }