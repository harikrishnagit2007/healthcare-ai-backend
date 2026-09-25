from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

documents = [
    "Fever can be associated with infection.",
    "Blood pressure can vary during the day.",
    "Dehydration may cause dizziness.",
    "Regular sleep supports overall health."
]

query = "I feel dizzy because I may not be drinking enough water."

document_embeddings = model.encode(documents)
query_embedding = model.encode([query])

scores = cosine_similarity(query_embedding, document_embeddings)[0]

for document, score in sorted(
    zip(documents, scores),
    key=lambda x: x[1],
    reverse=True
):
    print(f"{score:.4f} - {document}")