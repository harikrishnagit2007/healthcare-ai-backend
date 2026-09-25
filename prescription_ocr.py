import tkinter as tk
from tkinter import filedialog
import easyocr
import cv2

print("\n========== PRESCRIPTION OCR ==========\n")

root = tk.Tk()
root.withdraw()

image_path = filedialog.askopenfilename(
    title="Select Prescription Image",
    initialdir=r"C:\Users\kalpa\Downloads",
    filetypes=[
        ("Image files", "*.jpg *.jpeg *.png *.webp"),
        ("All files", "*.*")
    ]
)

if not image_path:
    print("No image selected.")
    exit()

print("Selected image:")
print(image_path)

print("\nLoading EasyOCR...")

reader = easyocr.Reader(["en"], gpu=False)

print("\nReading image...")

image = cv2.imread(image_path)

if image is None:
    print("ERROR: Could not open image.")
    exit()

results = reader.readtext(
    image,
    detail=1,
    paragraph=False,
    text_threshold=0.4,
    low_text=0.2,
    link_threshold=0.2,
    mag_ratio=2.0,
    canvas_size=3000
)

print("\n========== OCR RESULT ==========\n")

valid_results = []

for item in results:
    text = item[1].strip()
    confidence = float(item[2])

    if text:
        valid_results.append((text, confidence))

if not valid_results:
    print("No readable text detected.")
else:
    for text, confidence in valid_results:
        print(
            text
            + " | confidence: "
            + str(round(confidence, 4))
        )

print("\n========== STATUS ==========\n")

if not valid_results:
    print("OCR_STATUS: NO_TEXT")
elif len(valid_results) < 3:
    print("OCR_STATUS: LOW_TEXT")
else:
    print("OCR_STATUS: TEXT_DETECTED")

print("\nOCR output is raw extracted text.")
print("It must be verified before being used for medication information.")