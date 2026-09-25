from huggingface_hub import InferenceClient

client = InferenceClient()

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": "Say hello in one simple sentence."
        }
    ],
)

print("AI:", response.choices[0].message.content)