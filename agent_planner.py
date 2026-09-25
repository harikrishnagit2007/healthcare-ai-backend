import json
from datetime import datetime

from huggingface_hub import InferenceClient

from tool_registry import list_tools, execute_tool


# ============================================================
# CONFIG
# ============================================================

MODEL = "openai/gpt-oss-120b"
MAX_TOOL_ITERATIONS = 6
TRACE_FILE = "agent_planner_trace.json"


# ============================================================
# TOOL SCHEMAS
# ============================================================

TOOL_SCHEMAS = {
    "current_health": {
        "type": "function",
        "function": {
            "name": "current_health",
            "description": "Get the current synthetic patient health data.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },

    "previous_health": {
        "type": "function",
        "function": {
            "name": "previous_health",
            "description": "Get the previous synthetic patient health data.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },

    "compare_health": {
        "type": "function",
        "function": {
            "name": "compare_health",
            "description": "Compare current and previous health data.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },

    "what_matters_now": {
        "type": "function",
        "function": {
            "name": "what_matters_now",
            "description": "Return detected health changes that matter in the current project context.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },

    "current_symptoms": {
        "type": "function",
        "function": {
            "name": "current_symptoms",
            "description": "Get current synthetic patient symptoms.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },

    "previous_symptoms": {
        "type": "function",
        "function": {
            "name": "previous_symptoms",
            "description": "Get previous synthetic patient symptoms.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },

    "compare_symptoms": {
        "type": "function",
        "function": {
            "name": "compare_symptoms",
            "description": "Compare current and previous symptoms.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },

    "context_analysis": {
        "type": "function",
        "function": {
            "name": "context_analysis",
            "description": "Analyze the available healthcare context.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },

    "health_snapshot": {
        "type": "function",
        "function": {
            "name": "health_snapshot",
            "description": "Return a consolidated health snapshot.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },

    "decision_snapshot": {
        "type": "function",
        "function": {
            "name": "decision_snapshot",
            "description": "Return the current decision-support snapshot.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },

    "change_summary": {
        "type": "function",
        "function": {
            "name": "change_summary",
            "description": "Return a summary of detected health changes.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },

    "knowledge_retrieval": {
        "type": "function",
        "function": {
            "name": "knowledge_retrieval",
            "description": "Search the project knowledge base for information relevant to a query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The knowledge search query."
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Maximum number of results to retrieve.",
                        "default": 3
                    }
                },
                "required": [
                    "query"
                ],
                "additionalProperties": False
            }
        }
    }
}


# ============================================================
# BUILD MODEL TOOLS FROM REGISTRY
# ============================================================

def get_model_tools():
    registered_names = {
        tool.name
        for tool in list_tools()
    }

    model_tools = []

    for name in registered_names:
        if name in TOOL_SCHEMAS:
            model_tools.append(
                TOOL_SCHEMAS[name]
            )

    return model_tools


# ============================================================
# SAFE JSON SERIALIZATION
# ============================================================

def make_json_safe(value):
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


# ============================================================
# EXECUTE A REGISTERED TOOL
# ============================================================

def execute_agent_tool(
    tool_name,
    arguments
):
    available_names = {
        tool.name
        for tool in list_tools()
    }

    if tool_name not in available_names:
        raise ValueError(
            f"Unknown tool: {tool_name}"
        )

    if tool_name == "knowledge_retrieval":

        query = str(
            arguments.get(
                "query",
                ""
            )
        )

        top_k = int(
            arguments.get(
                "top_k",
                3
            )
        )

        raw_results = execute_tool(
            tool_name,
            query,
            top_k=top_k
        )

        results = []

        for item in raw_results:

            if (
                isinstance(item, tuple)
                and len(item) == 2
            ):
                document, score = item

                results.append(
                    {
                        "text": document.get(
                            "text",
                            str(document)
                        ),
                        "score": float(score)
                    }
                )

            else:
                results.append(
                    make_json_safe(item)
                )

        return {
            "query": query,
            "top_k": top_k,
            "results": results
        }

    return execute_tool(
        tool_name
    )


# ============================================================
# TRACE
# ============================================================

def create_trace():
    return {
        "agent_run_id": datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        ),
        "started_at": datetime.now().isoformat(),
        "iterations": [],
        "status": "running"
    }


def save_trace(trace):
    with open(
        TRACE_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            trace,
            file,
            indent=2,
            ensure_ascii=False,
            default=str
        )


# ============================================================
# AGENT
# ============================================================

def run_agent():

    trace = create_trace()

    model_tools = get_model_tools()

    print(
        "\n========== ADVANCED AGENT ==========\n"
    )

    print(
        "Registered tools:",
        len(model_tools)
    )

    print(
        "\nAvailable tools:"
    )

    for tool in model_tools:
        print(
            "-",
            tool["function"]["name"]
        )

    question = input(
        "\nAsk the healthcare agent:\n> "
    )

    client = InferenceClient()

    messages = [
        {
            "role": "system",
            "content": (
                "You are an advanced healthcare information "
                "agent for an educational synthetic-data prototype.\n\n"

                "You have access to backend tools.\n\n"

                "Choose tools dynamically based on the user's "
                "question.\n\n"

                "Do not call unrelated tools.\n"

                "You may call multiple tools when required.\n"

                "After receiving tool results, decide whether "
                "another tool is needed.\n\n"

                "Use tool results as the only source of "
                "patient-specific facts.\n\n"

                "Do not diagnose diseases.\n"
                "Do not prescribe medicines.\n"
                "Do not invent missing information.\n"
                "Do not infer unsupported medical relationships.\n\n"

                "All project patient information is synthetic "
                "test data."
            )
        },
        {
            "role": "user",
            "content": question
        }
    ]

    # ========================================================
    # AGENT LOOP
    # ========================================================

    for iteration in range(
        MAX_TOOL_ITERATIONS
    ):

        iteration_number = (
            iteration + 1
        )

        print(
            f"\n========== ITERATION "
            f"{iteration_number} ==========\n"
        )

        iteration_trace = {
            "iteration": iteration_number,
            "timestamp": datetime.now().isoformat(),
            "tool_calls": []
        }

        # ----------------------------------------------------
        # CALL MODEL
        # ----------------------------------------------------

        response = (
            client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=model_tools,
                tool_choice="auto"
            )
        )

        assistant_message = (
            response.choices[0].message
        )

        tool_calls = getattr(
            assistant_message,
            "tool_calls",
            None
        )

        # ----------------------------------------------------
        # FINAL RESPONSE
        # ----------------------------------------------------

        if not tool_calls:

            final_response = (
                assistant_message.content
                or "No response generated."
            )

            print(
                "\n========== FINAL RESPONSE ==========\n"
            )

            print(
                final_response
            )

            iteration_trace[
                "final_response"
            ] = final_response

            trace["iterations"].append(
                iteration_trace
            )

            trace["status"] = "completed"
            trace["finished_at"] = (
                datetime.now().isoformat()
            )

            save_trace(
                trace
            )

            print(
                "\nTrace saved to:",
                TRACE_FILE
            )

            return

        # ----------------------------------------------------
        # CONVERT ASSISTANT TOOL CALL MESSAGE
        # ----------------------------------------------------

        assistant_payload = {
            "role": "assistant",
            "content": (
                assistant_message.content
                or ""
            ),
            "tool_calls": []
        }

        for tool_call in tool_calls:

            function = tool_call.function

            raw_arguments = getattr(
                function,
                "arguments",
                "{}"
            )

            if isinstance(
                raw_arguments,
                dict
            ):
                arguments = raw_arguments
            else:
                try:
                    arguments = json.loads(
                        raw_arguments
                    )
                except (
                    json.JSONDecodeError,
                    TypeError
                ):
                    arguments = {}

            assistant_payload[
                "tool_calls"
            ].append(
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": function.name,
                        "arguments": json.dumps(
                            arguments
                        )
                    }
                }
            )

        messages.append(
            assistant_payload
        )

        # ----------------------------------------------------
        # EXECUTE TOOLS
        # ----------------------------------------------------

        for tool_call in tool_calls:

            function = tool_call.function

            tool_name = function.name

            raw_arguments = getattr(
                function,
                "arguments",
                "{}"
            )

            if isinstance(
                raw_arguments,
                dict
            ):
                arguments = raw_arguments
            else:
                try:
                    arguments = json.loads(
                        raw_arguments
                    )
                except (
                    json.JSONDecodeError,
                    TypeError
                ):
                    arguments = {}

            print(
                "Agent selected tool:",
                tool_name
            )

            print(
                "Arguments:",
                arguments
            )

            try:

                result = execute_agent_tool(
                    tool_name,
                    arguments
                )

                result_text = json.dumps(
                    make_json_safe(result),
                    indent=2,
                    ensure_ascii=False,
                    default=str
                )

                status = "success"

            except Exception as error:

                result_text = (
                    "TOOL EXECUTION ERROR: "
                    + type(error).__name__
                    + ": "
                    + str(error)
                )

                status = "error"

            print(
                "\nTool result:"
            )

            print(
                result_text
            )

            # ------------------------------------------------
            # SEND RESULT BACK TO MODEL
            # ------------------------------------------------

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": result_text
                }
            )

            # ------------------------------------------------
            # TRACE
            # ------------------------------------------------

            iteration_trace[
                "tool_calls"
            ].append(
                {
                    "tool": tool_name,
                    "arguments": arguments,
                    "status": status,
                    "result": result_text
                }
            )

        trace[
            "iterations"
        ].append(
            iteration_trace
        )

        save_trace(
            trace
        )

    # ========================================================
    # MAX ITERATIONS
    # ========================================================

    trace[
        "status"
    ] = "max_iterations_reached"

    trace[
        "finished_at"
    ] = datetime.now().isoformat()

    save_trace(
        trace
    )

    print(
        "\nAgent stopped after reaching "
        f"{MAX_TOOL_ITERATIONS} iterations."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:
        run_agent()

    except KeyboardInterrupt:
        print(
            "\nAgent stopped by user."
        )

    except Exception as error:

        print(
            "\n========== AGENT ERROR ==========\n"
        )

        print(
            type(error).__name__,
            ":",
            str(error)
        )