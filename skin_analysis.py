from transformers import pipeline

MODEL = "LaurianeMD/vit-skin-disease"
classifier = pipeline("image-classification", model=MODEL)

analyze_skin_image = lambda image_path: {
    "image": image_path,
    "results": [
        {
            "label": result["label"],
            "score": round(result["score"], 4)
        }
        for result in classifier(image_path)[:5]
    ],
    "note": "Image classification output for educational/research use. Not a medical diagnosis."
}