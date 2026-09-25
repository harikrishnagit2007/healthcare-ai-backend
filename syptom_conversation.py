import json
from huggingface_hub import InferenceClient

MODEL = "openai/gpt-oss-120b"
client = InferenceClient()

extract_symptom_information = lambda symptom_text: json.loads(
    client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract structured symptom information. "
                    "Use only information explicitly stated by the user. "
                    "Do not diagnose or infer."
                )
            },
            {
                "role": "user",
                "content": (
                    "Extract only information explicitly stated in the user's symptom description. "
                    "Return valid JSON with exactly these fields: "
                    "symptom, onset, duration, severity, body_location, associated_symptoms. "
                    "Use null when information is not provided. "
                    "Do not diagnose a disease. "
                    "Do not infer missing information. "
                    "Return JSON only.\n\n"
                    "User symptom description:\n"
                    + symptom_text
                )
            }
        ]
    ).choices[0].message.content
)