from huggingface_hub import InferenceClient

client = InferenceClient()

question = input("Ask the AI: ")

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": question
        }
    ],
)

answer = response.choices[0].message.content

print("\nAI:", answer)