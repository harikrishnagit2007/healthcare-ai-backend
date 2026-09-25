from transformers import pipeline

MODEL = "LaurianeMD/vit-skin-disease"

classifier = pipeline("image-classification", model=MODEL)

image_path = r"C:\Users\kalpa\Downloads\download.jpg"

results = classifier(image_path)

print("\n========== SKIN AI RESULTS ==========\n")
print("\n".join([
    result["label"] + " -> " + str(round(result["score"], 4))
    for result in results[:5]
]))