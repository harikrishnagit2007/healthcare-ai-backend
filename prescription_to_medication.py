from datetime import datetime
import re
import json
from prescription_parser import parse_prescription_text


def extract_duration_days(duration_text):
    if not duration_text:
        return None

    match = re.search(r"\d+", str(duration_text))

    if match:
        return int(match.group())

    return None


def convert_prescription_to_medication(parsed, reminder_times):
    duration_days = extract_duration_days(parsed.get("duration"))

    if not parsed.get("medicine_name"):
        return None

    if not duration_days:
        return None

    return {
        "medicine_name": parsed.get("medicine_name"),
        "purpose": "Not provided",
        "dosage": parsed.get("dosage"),
        "frequency": parsed.get("frequency"),
        "duration_days": duration_days,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "reminder_times": reminder_times,
        "status": "active"
    }


print("\n========== PRESCRIPTION TO MEDICATION ==========\n")

ocr_text = input("Enter OCR text:\n> ")

parsed_prescription = parse_prescription_text(ocr_text)

print("\n========== PARSED PRESCRIPTION ==========\n")
print(json.dumps(parsed_prescription, indent=2))

reminder_input = input(
    "\nEnter reminder times separated by commas "
    "(example: 09:00,21:00):\n> "
)

reminder_times = [
    time.strip()
    for time in reminder_input.split(",")
    if time.strip()
]

medication = convert_prescription_to_medication(
    parsed_prescription,
    reminder_times
)

print("\n========== MEDICATION RECORD ==========\n")

if medication:
    print(json.dumps(medication, indent=2))

    with open(
        "medication_record.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(medication, file, indent=2)

    print("\nMEDICATION_RECORD: SAVED")
else:
    print("MEDICATION_RECORD: NOT_SAVED")
    print(
        "\nRequired information was not detected."
    )
    print(
        "Medicine name:",
        parsed_prescription.get("medicine_name")
    )
    print(
        "Duration:",
        parsed_prescription.get("duration")
    )