from huggingface_hub import InferenceClient
from what_matters_now import get_what_matters_now
from retrieve_context import retrieve_context

client = InferenceClient()

what_matters = get_what_matters_now()

changes = "\n".join(
    f"- {change}" for change in what_matters["changes"]
)

if not changes:
    changes = "- No meaningful change was detected."

current_data = what_matters["current"]
previous_data = what_matters["previous"]

query = f"""
Current health data:
{current_data}

Previous health data:
{previous_data}

Detected changes:
{changes}
"""

results = retrieve_context(query, top_k=3)

print("WHAT MATTERS NOW?")
print(what_matters["status"])

print("\nCurrent Health:")
print(current_data)

print("\nPrevious Health:")
print(previous_data)

print("\nDetected Changes:")
print(changes)

print("\nRelevant Context:")
for doc, score in results:
    print(f"Score: {score:.4f}")
    print(doc["text"])
    print()

context = "\n".join(
    doc["text"] for doc, score in results
)

prompt = f"""
You are a healthcare information assistant.

WHAT MATTERS NOW:
{changes}

CURRENT HEALTH DATA:
{current_data}

PREVIOUS HEALTH DATA:
{previous_data}

RETRIEVED CONTEXT:
{context}

Explain the detected changes using only the retrieved context.

Rules:
- Do not diagnose.
- Do not prescribe medicines.
- Do not change medication doses.
- Do not invent medical facts.
- If the retrieved context is insufficient, say:
  "There is not enough information in the retrieved context."
- A change in a recorded value is not itself a diagnosis.
- Keep the explanation simple and clear.
- Recommend qualified professional review when appropriate.
"""

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

print("\nAI Agent Response:")
print(response.choices[0].message.content)