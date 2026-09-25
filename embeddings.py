from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

text = "The patient has a mild fever."

embedding = model.encode(text)

print("Embedding created successfully!")
print("Vector size:", len(embedding))
print("First 10 values:", embedding[:10])