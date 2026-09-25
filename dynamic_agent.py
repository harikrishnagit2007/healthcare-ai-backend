from huggingface_hub import InferenceClient
import json

from agent_tools import (
    current_health_tool,
    previous_health_tool,
    compare_health_tool,
    current_symptoms_tool,
    knowledge_retrieval_tool,
    what_matters_now_tool
)


client = InferenceClient()


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_health",
            "description": "Get the patient's latest recorded health data.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_previous_health",
            "description": "Get the patient's previous recorded health data.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_health",
            "description": "Compare the patient's current and previous health readings.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_symptoms",
            "description": "Get the patient's currently reported symptoms.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_health_knowledge",
            "description": "Retrieve relevant general healthcare information for the user's question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The health topic or question to search for."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_what_matters_now",
            "description": "Identify meaningful changes in the patient's recorded health data compared with previous records.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


def run_tool(name, arguments):

    if name == "get_current_health":
        return current_health_tool()

    if name == "get_previous_health":
        return previous_health_tool()

    if name == "compare_health":
        return compare_health_tool()

    if name == "get_current_symptoms":
        return current_symptoms_tool()

    if name == "retrieve_health_knowledge":
        return knowledge_retrieval_tool(
            arguments["query"],
            top_k=3
        )

    if name == "get_what_matters_now":
        return what_matters_now_tool()

    return {
        "error": f"Unknown tool: {name}"
    }


def main():

    question = input("Ask the health agent: ")

    messages = [
        {
            "role": "system",
            "content": """
You are a healthcare information assistant.

Use the available tools when they are useful.

Rules:
- Do not diagnose.
- Do not prescribe medicines.
- Do not change medication doses.
- Treat health values as recorded information, not a diagnosis.
- Use retrieved knowledge only as supporting information.
- Give a simple and clear response.
- Never change, guess, round, or invent patient values.
- Copy dates, numbers, units, and measurements exactly from tool results.
- Never replace a recorded date with a different year or date."""
        },
        {
            "role": "user",
            "content": question
        }
    ]

    while True:

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message

        if not message.tool_calls:
            print("\nAI Agent:")
            print(message.content)
            break

        # Add the assistant tool-call message
        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments or "{}"
                        }
                    }
                    for tool_call in message.tool_calls
                ]
            }
        )

        print("\nTools selected by the agent:")

        # Execute selected tools
        for tool_call in message.tool_calls:

            tool_name = tool_call.function.name
            arguments_text = tool_call.function.arguments or "{}"

            arguments = json.loads(arguments_text)

            print("-", tool_name)

            result = run_tool(
                tool_name,
                arguments
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                }
            )


if __name__ == "__main__":
    main()