import json
from huggingface_hub import InferenceClient

MODEL = "openai/gpt-oss-120b"

client = InferenceClient()

user_text = input("Describe your symptom:\n> ")

prompt = (
"You are a healthcare symptom-information parser for a software prototype. "
"Do not diagnose a disease. "
"Extract only information explicitly stated by the user. "
"Do not guess missing information. "
"Return JSON with exactly these fields: "
"symptom, onset, duration, severity, body_location, associated_symptoms. "
"Use null when information is not provided. "
"associated_symptoms must be a list. "
"\n\nUSER INPUT:\n"
+ user_text
)

response = client.chat.completions.create(
model=MODEL,
messages=[
{
"role": "system",
"content": (
"Return only valid JSON. "
"Do not diagnose or recommend treatment."
)
},
{
"role": "user",
"content": prompt
}
]
)

text = response.choices[0].message.content

result = json.loads(text)

print("\n========== STRUCTURED SYMPTOM DATA ==========\n")
print(json.dumps(result, indent=2))
