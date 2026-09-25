import json
from datetime import datetime
from transformers import AutoImageProcessor
from transformers import XLMRobertaTokenizer
from transformers import VisionEncoderDecoderModel
from PIL import Image
from prescription_parser import parse_prescription_text


MODEL = "microsoft/trocr-small-printed"


print("\n========== PRESCRIPTION TO MEDICATION PIPELINE ==========\n")

image_path = input("Prescription image path:\n> ")

print("\nLoading OCR model...")

image_processor = AutoImageProcessor.from_pretrained(MODEL)
tokenizer = XLMRobertaTokenizer.from_pretrained(MODEL)
model = VisionEncoderDecoderModel.from_pretrained(MODEL)

print("\nReading prescription image...")

image = Image.open(image_path).convert("RGB")

pixel_values = image_processor(
    images=image,
    return_tensors="pt"
).pixel_values

generated_ids = model.generate(
    pixel_values,
    max_new_tokens=64
)

ocr_text = tokenizer.batch_decode(
    generated_ids,
    skip_special_tokens=True
)[0]

print("\n========== OCR TEXT ==========\n")
print(ocr_text)

if not ocr_text.strip():
    print("\nNo OCR text was extracted.")
    print("MEDICATION_RECORD: NOT_SAVED")
    raise SystemExit

print("\nParsing OCR text...")

parsed = parse_prescription_text(ocr_text)

print("\n========== PARSED PRESCRIPTION ==========\n")
print(json.dumps(parsed, indent=2))

reminder_input = input(
    "\nEnter reminder times separated by commas "
    "(example: 09:00,21:00):\n> "
)

reminder_times = [
    time.strip()
    for time in reminder_input.split(",")
    if time.strip()
]

duration_text = parsed.get("duration")

duration_days = None

if duration_text:
    digits = "".join(
        character
        for character in str(duration_text)
        if character.isdigit()
    )

    if digits:
        duration_days = int(digits)

if not parsed.get("medicine_name"):
    print("\nMEDICATION_RECORD: NOT_SAVED")
    print("Medicine name was not detected.")
    raise SystemExit

if not duration_days:
    print("\nMEDICATION_RECORD: NOT_SAVED")
    print("Duration was not detected.")
    raise SystemExit

if not reminder_times:
    print("\nMEDICATION_RECORD: NOT_SAVED")
    print("No reminder times were provided.")
    raise SystemExit

medication_record = {
    "medicine_name": parsed.get("medicine_name"),
    "purpose": "Not provided",
    "dosage": parsed.get("dosage"),
    "frequency": parsed.get("frequency"),
    "duration_days": duration_days,
    "start_date": datetime.now().strftime("%Y-%m-%d"),
    "reminder_times": reminder_times,
    "status": "active"
}

with open(
    "medication_record.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        medication_record,
        file,
        indent=2
    )

print("\n========== MEDICATION RECORD ==========\n")
print(json.dumps(medication_record, indent=2))

print("\nMEDICATION_RECORD: SAVED")

print(
    "\nOCR-derived information must be verified "
    "against the original prescription."
)

print("This pipeline does not diagnose or prescribe.")