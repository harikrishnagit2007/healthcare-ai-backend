from huggingface_hub import InferenceClient
from retrieve_context import retrieve_context

client = InferenceClient()

question = input("Ask a health-related question: ")

results = retrieve_context(question)

print("\nRetrieved context:\n")

for doc, score in results:
    print(f"Score: {score:.4f}")
    print(doc["text"])
    print()

context = "\n".join(
    doc["text"] for doc, score in results
)

prompt = f"""
You are a healthcare information assistant.

Use only the provided context.

Rules:
- Do not diagnose.
- Do not prescribe medicines.
- Do not change medication doses.
- Do not invent medical facts.
- If the context does not contain enough information, say:
  "I don't have enough information in the provided context."
- Keep the response simple.

Context:
{context}

User question:
{question}
"""

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ],
)

print("\nAI Response:")
print(response.choices[0].message.content)