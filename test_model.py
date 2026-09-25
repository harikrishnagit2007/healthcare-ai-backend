from transformers import pipeline

classifier = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english"
)

result = classifier("Hugging Face makes NLP so easy!")

print(result)