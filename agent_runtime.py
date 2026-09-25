import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from huggingface_hub import InferenceClient

from tool_registry import list_tools
from tool_registry import execute_tool


# ============================================================
# CONFIGURATION
# ============================================================

MODEL = "openai/gpt-oss-120b"

TRACE_FILE = "agent_full_scan_trace.json"

MAX_WORKERS = 6


# ============================================================
# TOOL EXECUTION
# ============================================================

def execute_one_tool(
    tool_name,
    question
):
    started = datetime.now()

    try:

        # ----------------------------------------------------
        # Knowledge retrieval needs the user's question.
        # Every other current project tool is called with no args.
        # ----------------------------------------------------

        if tool_name == "knowledge_retrieval":

            result = execute_tool(
                tool_name,
                question,
                top_k=3
            )

        else:

            result = execute_tool(
                tool_name
            )

        finished = datetime.now()

        latency_ms = round(
            (
                finished - started
            ).total_seconds() * 1000,
            2
        )

        return {
            "tool": tool_name,
            "status": "WORKING",
            "latency_ms": latency_ms,
            "result": result
        }

    except Exception as error:

        finished = datetime.now()

        latency_ms = round(
            (
                finished - started
            ).total_seconds() * 1000,
            2
        )

        return {
            "tool": tool_name,
            "status": "FAILED",
            "latency_ms": latency_ms,
            "error_type": type(error).__name__,
            "error": str(error)
        }


# ============================================================
# SAFE JSON CONVERSION
# ============================================================

def make_json_safe(value):

    try:
        json.dumps(
            value,
            default=str
        )

        return value

    except TypeError:

        return str(value)


# ============================================================
# FULL TOOL SCAN
# ============================================================

def scan_all_tools(
    question
):
    """
    IMPORTANT:

    This function intentionally checks EVERY registered tool
    for EVERY user question.

    No intent-based filtering happens here.
    """

    registered = list_tools()

    tool_names = [
        tool.name
        for tool in registered
    ]

    print(
        "\n========== FULL TOOL SCAN ==========\n"
    )

    print(
        "Total registered tools:",
        len(tool_names)
    )

    for tool_name in tool_names:
        print(
            "-",
            tool_name
        )

    print(
        "\nChecking ALL tools...\n"
    )

    results = []

    # --------------------------------------------------------
    # Execute all read-only tools.
    # --------------------------------------------------------
    #
    # We use a thread pool because these project tools are
    # independent read operations.
    #
    # Results are reordered later to match registry order.
    # --------------------------------------------------------

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = {
            executor.submit(
                execute_one_tool,
                tool_name,
                question
            ): tool_name
            for tool_name in tool_names
        }

        completed_results = {}

        for future in as_completed(
            futures
        ):

            tool_name = futures[
                future
            ]

            try:

                result = future.result()

            except Exception as error:

                result = {
                    "tool": tool_name,
                    "status": "FAILED",
                    "error_type": type(error).__name__,
                    "error": str(error)
                }

            completed_results[
                tool_name
            ] = result

            print(
                f"[{result['status']}] "
                f"{tool_name}"
            )

    # --------------------------------------------------------
    # Preserve registry order
    # --------------------------------------------------------

    for tool_name in tool_names:

        results.append(
            completed_results[
                tool_name
            ]
        )

    return results


# ============================================================
# BUILD AGENT CONTEXT
# ============================================================

def build_context(
    question,
    tool_results
):

    context = {
        "user_question": question,
        "tool_scan_policy": (
            "Every registered tool was checked before "
            "the final answer."
        ),
        "tools": []
    }

    for item in tool_results:

        safe_result = item.copy()

        if "result" in safe_result:

            safe_result[
                "result"
            ] = make_json_safe(
                safe_result["result"]
            )

        context[
            "tools"
        ].append(
            safe_result
        )

    return context


# ============================================================
# TRACE
# ============================================================

def create_trace(
    question
):

    return {
        "run_id": datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        ),
        "started_at": datetime.now().isoformat(),
        "question": question,
        "policy": (
            "ALL registered tools are checked for every "
            "user question before final response."
        ),
        "tool_results": [],
        "status": "running"
    }


def save_trace(
    trace
):

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
# FINAL ANALYSIS
# ============================================================

def generate_final_response(
    question,
    tool_results
):

    client = InferenceClient()

    context = build_context(
        question,
        tool_results
    )

    system_prompt = """
You are the final analysis layer of an educational
healthcare information prototype.

IMPORTANT OPERATING RULE:

Every registered backend tool has already been checked
for the user's question.

You must analyze ALL supplied tool results before writing
the final response.

Do not ignore a tool merely because it appears unrelated.

Use only the supplied tool results for patient-specific facts.

Do not invent missing information.

Do not diagnose diseases.

Do not prescribe medicines.

Do not recommend changing medication instructions.

Do not create unsupported medical relationships.

Clearly state when project patient data is synthetic
test data.

If a tool failed, acknowledge that the tool result was
unavailable rather than inventing its information.

Structure the final answer clearly and distinguish:
1. Information found
2. Important changes detected by the project's tools
3. Medication/reminder information when available
4. Knowledge retrieved from the project knowledge base
5. Tools that failed, if any

This is an educational decision-support prototype,
not a medical diagnosis system.
"""

    user_message = (
        "USER QUESTION:\n"
        + question
        + "\n\n"
        + "COMPLETE TOOL SCAN RESULTS:\n"
        + json.dumps(
            context,
            indent=2,
            ensure_ascii=False,
            default=str
        )
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    return (
        response.choices[0].message.content
        or "No final response was generated."
    )


# ============================================================
# MAIN AGENT
# ============================================================

def run_agent():

    question = input(
        "\nAsk the healthcare agent:\n> "
    )

    trace = create_trace(
        question
    )

    print(
        "\n========== ADVANCED HEALTHCARE AGENT ==========\n"
    )

    print(
        "Policy: CHECK ALL TOOLS FOR EVERY QUESTION"
    )

    # --------------------------------------------------------
    # STEP 1: EVERY TOOL IS CHECKED
    # --------------------------------------------------------

    tool_results = scan_all_tools(
        question
    )

    trace[
        "tool_results"
    ] = tool_results

    # --------------------------------------------------------
    # TOOL SUMMARY
    # --------------------------------------------------------

    working = [
        item
        for item in tool_results
        if item["status"] == "WORKING"
    ]

    failed = [
        item
        for item in tool_results
        if item["status"] == "FAILED"
    ]

    print(
        "\n========== TOOL SCAN COMPLETE ==========\n"
    )

    print(
        "Total tools checked:",
        len(tool_results)
    )

    print(
        "Working:",
        len(working)
    )

    print(
        "Failed:",
        len(failed)
    )

    # --------------------------------------------------------
    # STEP 2: FINAL AI ANALYSIS
    # --------------------------------------------------------

    print(
        "\n========== ANALYZING ALL TOOL RESULTS ==========\n"
    )

    try:

        final_response = generate_final_response(
            question,
            tool_results
        )

        print(
            "\n========== FINAL AGENT RESPONSE ==========\n"
        )

        print(
            final_response
        )

        trace[
            "status"
        ] = "completed"

        trace[
            "final_response"
        ] = final_response

    except Exception as error:

        print(
            "\n========== FINAL ANALYSIS ERROR ==========\n"
        )

        print(
            type(error).__name__,
            ":",
            str(error)
        )

        trace[
            "status"
        ] = "final_analysis_failed"

        trace[
            "error"
        ] = str(error)

    trace[
        "finished_at"
    ] = datetime.now().isoformat()

    save_trace(
        trace
    )

    print(
        "\nTrace saved to:",
        TRACE_FILE
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