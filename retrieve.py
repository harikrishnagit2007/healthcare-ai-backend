from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from knowledge_base import documents

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def retrieve_knowledge(query, top_k=3): return [
{
"text": document["text"],
"score": round(float(score), 4)
}
for document, score in sorted(
zip(
documents,
cosine_similarity(
model.encode([query]),
model.encode([document["text"] for document in documents])
)[0]
),
key=lambda item: item[1],
reverse=True
)[:top_k]
]
