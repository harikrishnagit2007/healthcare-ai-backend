from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

sentence1 = "The patient has a mild fever."
sentence2 = "The patient has a slightly high temperature."

embedding1 = model.encode([sentence1])
embedding2 = model.encode([sentence2])

similarity = cosine_similarity(embedding1, embedding2)

print("Sentence 1:", sentence1)
print("Sentence 2:", sentence2)
print("Similarity score:", similarity[0][0])