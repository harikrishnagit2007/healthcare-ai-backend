import re


def parse_prescription_text(ocr_lines):

    medicine_name = "Not detected"
    dosage = "Not detected"
    frequency = "Not detected"
    duration = "Not detected"

    lines = [
        str(line).strip()
        for line in ocr_lines
        if str(line).strip()
    ]

    for line in lines:

        lower = line.lower()

        if dosage == "Not detected":

            match = re.search(
                r"\b\d+(?:\.\d+)?\s*(mg|g|mcg|ml|mg/ml)\b",
                line,
                re.IGNORECASE
            )

            if match:
                dosage = match.group(0)

        if frequency == "Not detected":

            if re.search(r"\b1[-/ ]?0[-/ ]?1\b", line):
                frequency = "1-0-1"

            elif re.search(r"\b0[-/ ]?1[-/ ]?0\b", line):
                frequency = "0-1-0"

            elif re.search(r"\b1[-/ ]?0[-/ ]?0\b", line):
                frequency = "1-0-0"

            elif re.search(r"\b0[-/ ]?0[-/ ]?1\b", line):
                frequency = "0-0-1"

            elif "once daily" in lower or "once a day" in lower:
                frequency = "once daily"

            elif "twice daily" in lower or "twice a day" in lower:
                frequency = "twice daily"

            elif "three times daily" in lower or "three times a day" in lower:
                frequency = "three times daily"

        if duration == "Not detected":

            match = re.search(
                r"\b\d+\s*(day|days|week|weeks)\b",
                line,
                re.IGNORECASE
            )

            if match:
                duration = match.group(0)

    candidates = []

    for line in lines:

        lower = line.lower()

        if (
            re.search(
                r"\b\d+(?:\.\d+)?\s*(mg|g|mcg|ml)\b",
                line,
                re.IGNORECASE
            )
            or "tablet" in lower
            or "capsule" in lower
            or "syrup" in lower
            or "cream" in lower
            or "ointment" in lower
        ):
            candidates.append(line)

    if candidates:

        medicine_name = candidates[0]

        medicine_name = re.sub(
            r"\b\d+(?:\.\d+)?\s*(mg|g|mcg|ml)\b",
            "",
            medicine_name,
            flags=re.IGNORECASE
        )

        medicine_name = re.sub(
            r"\b\d+\s*(day|days|week|weeks)\b",
            "",
            medicine_name,
            flags=re.IGNORECASE
        )

        medicine_name = re.sub(
            r"\b(tablet|tablets|capsule|capsules|syrup|cream|ointment)\b",
            "",
            medicine_name,
            flags=re.IGNORECASE
        )

        medicine_name = medicine_name.strip(" -:,")

    return {
        "medicine_name": medicine_name,
        "dosage": dosage,
        "frequency": frequency,
        "duration": duration
    }