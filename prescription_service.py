import json
import re
from datetime import datetime

import torch
from PIL import Image
from transformers import AutoImageProcessor
from transformers import XLMRobertaTokenizer
from transformers import VisionEncoderDecoderModel

from prescription_parser import parse_prescription_text


MODEL = "microsoft/trocr-small-printed"
MEDICATION_FILE = "medication_record.json"

print("Loading prescription OCR model...")

image_processor = AutoImageProcessor.from_pretrained(MODEL)
tokenizer = XLMRobertaTokenizer.from_pretrained(MODEL)
model = VisionEncoderDecoderModel.from_pretrained(MODEL)
model.eval()


def extract_duration_days(duration_text):
    if not duration_text:
        return None

    match = re.search(r"\d+", str(duration_text))

    if match:
        return int(match.group())

    return None


def run_prescription_ocr(image_path):
    image = Image.open(image_path).convert("RGB")

    pixel_values = image_processor(
        images=image,
        return_tensors="pt"
    ).pixel_values

    with torch.no_grad():
        generated_ids = model.generate(
            pixel_values,
            max_new_tokens=64
        )

    return tokenizer.batch_decode(
        generated_ids,
        skip_special_tokens=True
    )[0]


def create_medication_record(parsed, reminder_times):
    duration_days = extract_duration_days(
        parsed.get("duration")
    )

    medicine_name = parsed.get(
        "medicine_name"
    )

    if not medicine_name:
        return None, "Medicine name was not detected."

    if not duration_days:
        return None, "Duration was not detected."

    if not reminder_times:
        return None, "Reminder times were not provided."

    medication_record = {
        "medicine_name": medicine_name,
        "purpose": "Not provided",
        "dosage": parsed.get("dosage"),
        "frequency": parsed.get("frequency"),
        "duration_days": duration_days,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "reminder_times": reminder_times,
        "status": "active"
    }

    return medication_record, None


def process_prescription(
    image_path,
    reminder_times
):
    ocr_text = run_prescription_ocr(
        image_path
    )

    if not ocr_text.strip():
        return {
            "status": "NOT_SAVED",
            "reason": "No OCR text was extracted.",
            "ocr_text": "",
            "prescription": None,
            "medication_record": None
        }

    parsed = parse_prescription_text(
        ocr_text
    )

    medication_record, error = (
        create_medication_record(
            parsed,
            reminder_times
        )
    )

    if error:
        return {
            "status": "NOT_SAVED",
            "reason": error,
            "ocr_text": ocr_text,
            "prescription": parsed,
            "medication_record": None
        }

    with open(
        MEDICATION_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            medication_record,
            file,
            indent=2
        )

    return {
        "status": "SAVED",
        "ocr_text": ocr_text,
        "prescription": parsed,
        "medication_record": medication_record,
        "note": (
            "OCR-derived information must be "
            "verified against the original prescription. "
            "This pipeline does not diagnose or prescribe."
        )
    }