from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from knowledge_base import documents

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def retrieve_context(query, top_k=3):
    texts = [doc["text"] for doc in documents]

    document_embeddings = model.encode(texts)
    query_embedding = model.encode([query])

    scores = cosine_similarity(
        query_embedding,
        document_embeddings
    )[0]

    ranked = sorted(
        zip(documents, scores),
        key=lambda x: x[1],
        reverse=True
    )

    return ranked[:top_k]