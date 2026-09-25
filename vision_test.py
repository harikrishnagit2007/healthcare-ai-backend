from transformers import pipeline

MODEL = "google/vit-base-patch16-224"

classifier = pipeline(
"image-classification",
model=MODEL
)

image_path = r"C:\Users\kalpa\Downloads\download.jpg"

results = classifier(image_path)

print("\n========== IMAGE AI RESULTS ==========\n")

print(
"\n".join(
[
result["label"] + " -> " + str(round(result["score"], 4))
for result in results[:5]
]
)
)
