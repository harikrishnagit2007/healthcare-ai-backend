from transformers import pipeline

generator = pipeline(
    "text-generation",
    model="gpt2"
)

result = generator(
    "AI in healthcare can",
    max_length=30
)

print(result)