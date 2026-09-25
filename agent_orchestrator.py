import asyncio
import json
import os
from datetime import datetime

from huggingface_hub import InferenceClient
from mcp import Client, StdioServerParameters


# ============================================================
# CONFIGURATION
# ============================================================

MODEL = "openai/gpt-oss-120b"

PROJECT_DIR = (
    r"C:\Users\kalpa\OneDrive\Desktop\hugging face"
)

SERVER_PATH = os.path.join(
    PROJECT_DIR,
    "mcp_patient_server.py"
)

MAX_TOOL_ITERATIONS = 6

TRACE_FILE = os.path.join(
    PROJECT_DIR,
    "agent_trace.json"
)


# ============================================================
# ALLOWED MCP TOOLS
# ============================================================

READ_ONLY_TOOLS = {
    "get_patient_current_health",
    "get_patient_previous_health",
    "compare_patient_health",
    "get_patient_symptoms",
    "get_patient_what_matters_now"
}


# ============================================================
# TRACE FUNCTIONS
# ============================================================

def create_trace():
    return {
        "agent_run_id": datetime.now().strftime(
            "%Y%m%d_%H%M%S"
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
# MCP → LLM TOOL FORMAT
# ============================================================

def convert_mcp_tool(tool):
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema
        }
    }


# ============================================================
# MCP RESULT → TEXT
# ============================================================

def extract_tool_result(result):
    output = []

    for content_block in result.content:
        text_value = getattr(
            content_block,
            "text",
            None
        )

        if text_value is not None:
            output.append(text_value)

    if output:
        return "\n".join(output)

    structured = getattr(
        result,
        "structured_content",
        None
    )

    if structured is not None:
        return json.dumps(
            structured,
            indent=2,
            ensure_ascii=False,
            default=str
        )

    return "{}"


# ============================================================
# HUGGING FACE ASSISTANT MESSAGE → DICT
# ============================================================

def assistant_message_to_dict(
    assistant_message
):
    message = {
        "role": "assistant",
        "content": assistant_message.content or ""
    }

    tool_calls = getattr(
        assistant_message,
        "tool_calls",
        None
    )

    if tool_calls:

        message["tool_calls"] = []

        for tool_call in tool_calls:

            function = tool_call.function

            arguments = getattr(
                function,
                "arguments",
                "{}"
            )

            if isinstance(arguments, dict):
                arguments = json.dumps(
                    arguments
                )

            message["tool_calls"].append(
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": function.name,
                        "arguments": str(
                            arguments
                        )
                    }
                }
            )

    return message


# ============================================================
# PARSE TOOL ARGUMENTS
# ============================================================

def parse_arguments(raw_arguments):

    if isinstance(
        raw_arguments,
        dict
    ):
        return raw_arguments

    if not raw_arguments:
        return {}

    try:
        return json.loads(
            raw_arguments
        )
    except (
        json.JSONDecodeError,
        TypeError
    ):
        return {}


# ============================================================
# MAIN AGENT
# ============================================================

async def run_agent():

    trace = create_trace()

    server_parameters = StdioServerParameters(
        command="python",
        args=[
            SERVER_PATH
        ],
        cwd=PROJECT_DIR
    )

    print(
        "\n========== ADVANCED MCP AGENT ==========\n"
    )

    print(
        "Starting MCP Patient Server..."
    )

    async with Client(
        server_parameters
    ) as mcp_client:

        print(
            "MCP connection: OK"
        )

        print(
            "Protocol version:",
            mcp_client.protocol_version
        )

        print(
            "Server info:",
            mcp_client.server_info
        )

        # ----------------------------------------------------
        # DISCOVER MCP TOOLS
        # ----------------------------------------------------

        tools_result = (
            await mcp_client.list_tools()
        )

        discovered_tools = (
            tools_result.tools
        )

        llm_tools = [
            convert_mcp_tool(tool)
            for tool in discovered_tools
        ]

        print(
            "\n========== DISCOVERED MCP TOOLS ==========\n"
        )

        for tool in discovered_tools:
            print(
                f"- {tool.name}"
            )

        # ----------------------------------------------------
        # USER QUESTION
        # ----------------------------------------------------

        question = input(
            "\nAsk the healthcare agent:\n> "
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an orchestration agent for an "
                    "educational healthcare prototype.\n\n"

                    "Use MCP tools whenever patient-specific "
                    "information is required.\n\n"

                    "Patient-specific facts must come only "
                    "from MCP tool results.\n\n"

                    "Do not invent patient information.\n"
                    "Do not diagnose diseases.\n"
                    "Do not prescribe medicines.\n"
                    "Do not infer causes or relationships "
                    "unless explicitly supported by tool results.\n\n"

                    "The available MCP tools are read-only.\n"
                    "Do not attempt write operations.\n\n"

                    "Clearly state that the patient data is "
                    "synthetic test data."
                )
            },
            {
                "role": "user",
                "content": question
            }
        ]

        # ----------------------------------------------------
        # AGENT LOOP
        # ----------------------------------------------------

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

            # ------------------------------------------------
            # ASK LLM
            # ------------------------------------------------

            response = (
                InferenceClient()
                .chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=llm_tools,
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

            # ------------------------------------------------
            # NO TOOL CALL → FINAL ANSWER
            # ------------------------------------------------

            if not tool_calls:

                final_text = (
                    assistant_message.content
                    or "No response generated."
                )

                print(
                    "\n========== FINAL RESPONSE ==========\n"
                )

                print(
                    final_text
                )

                iteration_trace[
                    "final_response"
                ] = final_text

                trace["iterations"].append(
                    iteration_trace
                )

                trace["status"] = (
                    "completed"
                )

                trace["finished_at"] = (
                    datetime.now().isoformat()
                )

                save_trace(trace)

                print(
                    "\nAgent trace saved to:"
                )

                print(
                    TRACE_FILE
                )

                return

            # ------------------------------------------------
            # ADD ASSISTANT TOOL-CALL MESSAGE
            # ------------------------------------------------

            assistant_dict = (
                assistant_message_to_dict(
                    assistant_message
                )
            )

            messages.append(
                assistant_dict
            )

            # ------------------------------------------------
            # EXECUTE EACH MCP TOOL
            # ------------------------------------------------

            for tool_call in tool_calls:

                tool_name = (
                    tool_call.function.name
                )

                raw_arguments = (
                    tool_call.function.arguments
                )

                arguments = parse_arguments(
                    raw_arguments
                )

                print(
                    f"Requested MCP tool: "
                    f"{tool_name}"
                )

                print(
                    "Arguments:",
                    arguments
                )

                # --------------------------------------------
                # SAFETY / PERMISSION CHECK
                # --------------------------------------------

                if tool_name not in READ_ONLY_TOOLS:

                    blocked_result = (
                        "TOOL BLOCKED: "
                        "Only approved read-only "
                        "healthcare tools may be called."
                    )

                    print(
                        blocked_result
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": blocked_result
                        }
                    )

                    iteration_trace[
                        "tool_calls"
                    ].append(
                        {
                            "tool": tool_name,
                            "arguments": arguments,
                            "status": "blocked"
                        }
                    )

                    continue

                # --------------------------------------------
                # CALL MCP TOOL
                # --------------------------------------------

                try:

                    tool_result = (
                        await mcp_client.call_tool(
                            tool_name,
                            arguments
                        )
                    )

                    result_text = (
                        extract_tool_result(
                            tool_result
                        )
                    )

                    result_status = (
                        "error"
                        if tool_result.is_error
                        else "success"
                    )

                except Exception as error:

                    result_text = (
                        "MCP tool execution failed: "
                        + str(error)
                    )

                    result_status = "error"

                print(
                    "\nTool result:"
                )

                print(
                    result_text
                )

                # --------------------------------------------
                # GIVE TOOL RESULT BACK TO LLM
                # --------------------------------------------

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": result_text
                    }
                )

                # --------------------------------------------
                # TRACE
                # --------------------------------------------

                iteration_trace[
                    "tool_calls"
                ].append(
                    {
                        "tool": tool_name,
                        "arguments": arguments,
                        "status": result_status,
                        "result": result_text
                    }
                )

            # ------------------------------------------------
            # SAVE TRACE AFTER EVERY ITERATION
            # ------------------------------------------------

            trace["iterations"].append(
                iteration_trace
            )

            save_trace(trace)

        # ----------------------------------------------------
        # MAX ITERATIONS
        # ----------------------------------------------------

        trace["status"] = (
            "max_iterations_reached"
        )

        trace["finished_at"] = (
            datetime.now().isoformat()
        )

        save_trace(trace)

        print(
            "\nAgent stopped after reaching "
            f"{MAX_TOOL_ITERATIONS} tool iterations."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:
        asyncio.run(
            run_agent()
        )

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
            error
        )