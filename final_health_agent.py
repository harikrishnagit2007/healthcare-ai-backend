import json
from huggingface_hub import InferenceClient

from agent_tools import what_matters_now_tool
from agent_tools import knowledge_retrieval_tool

MODEL = "openai/gpt-oss-120b"

client = InferenceClient()

question = input("Ask the health agent:\n> ")

# Get the current synthetic health-change information

what_matters = what_matters_now_tool()

# Always retrieve information from the local knowledge base

knowledge = knowledge_retrieval_tool(
question,
top_k=3
)

grounded_context = (
"USER QUESTION:\n"
+ question
+ "\n\n"
+ "WHAT MATTERS NOW:\n"
+ json.dumps(what_matters, default=str)
+ "\n\n"
+ "RETRIEVED LOCAL KNOWLEDGE:\n"
+ json.dumps(knowledge, default=str)
)

system_message = (
"You are a healthcare decision-support software prototype. "
"All patient data is synthetic test data. "
"Answer using only the supplied health data and retrieved local knowledge. "
"Do not diagnose diseases. "
"Do not prescribe medicines. "
"Do not invent causes, treatments, warnings, or medical facts. "
"If the retrieved knowledge does not contain enough information, "
"say that there is not enough information in the local knowledge base. "
"Keep the answer simple and grounded."
)

messages = [
{
"role": "system",
"content": system_message
},
{
"role": "user",
"content": grounded_context
}
]

print("\n========== KNOWLEDGE RETRIEVAL ==========\n")
print(json.dumps(knowledge, indent=2, default=str))

print("\n========== WHAT MATTERS NOW ==========\n")
print(json.dumps(what_matters, indent=2, default=str))

print("\n========== AI RESPONSE ==========\n")

response = client.chat.completions.create(
model=MODEL,
messages=messages
)

print(response.choices[0].message.content)
