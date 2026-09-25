from huggingface_hub import InferenceClient
from what_matters_now import get_what_matters_now

client = InferenceClient()

what_matters = get_what_matters_now()

changes = "\n".join(
    f"- {change}" for change in what_matters["changes"]
)

if not changes:
    changes = "- No meaningful change was detected."

prompt = f"""
You are a healthcare information assistant.

The system detected the following changes in a patient's health records:

{changes}

Explain these changes in simple language.

Rules:
- Do not diagnose.
- Do not prescribe medicines.
- Do not change medication doses.
- Do not invent medical facts.
- Explain that these are changes in recorded data, not a diagnosis.
- Recommend professional review when appropriate.
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

print("WHAT MATTERS NOW?")
print(what_matters["status"])

print("\nAI Agent Response:")
print(response.choices[0].message.content)