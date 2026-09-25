import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_id = "distilbert-base-uncased-finetuned-sst-2-english"

tokenizer = AutoTokenizer.from_pretrained(model_id)

model = AutoModelForSequenceClassification.from_pretrained(model_id)

inputs = tokenizer("Great course material!", return_tensors="pt")

outputs = model(**inputs)

print(outputs.logits)

probabilities = torch.softmax(outputs.logits, dim=1)

print(probabilities)

predicted_class = torch.argmax(probabilities, dim=1).item()

labels = ["NEGATIVE", "POSITIVE"]

prediction = labels[predicted_class]

confidence = probabilities[0][predicted_class].item() * 100

print("Prediction:", prediction)
print("Confidence:", f"{confidence:.2f}%")