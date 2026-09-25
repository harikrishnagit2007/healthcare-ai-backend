from dataclasses import dataclass
from typing import Callable, Any


# ============================================================
# TOOL DEFINITION
# ============================================================

@dataclass
class ToolDefinition:
    name: str
    description: str
    function: Callable
    category: str
    read_only: bool = True


# ============================================================
# IMPORT YOUR EXISTING TOOLS
# ============================================================

from health_tools import get_current_health
from previous_health import get_previous_health
from compare_health import compare_health

from what_matters_now import get_what_matters_now

from symptom_tools import get_current_symptoms
from previous_symptoms import get_previous_symptoms
from compare_symptoms import compare_symptoms

from context_analysis import analyze_context
from health_snapshot import get_health_snapshot
from decision_snapshot import get_decision_snapshot
from change_summary import get_change_summary

from retrieve_context import retrieve_context


# ============================================================
# TOOL REGISTRY
# ============================================================

TOOLS = {

    "current_health": ToolDefinition(
        name="current_health",
        description=(
            "Get the current synthetic patient health data."
        ),
        function=get_current_health,
        category="health"
    ),

    "previous_health": ToolDefinition(
        name="previous_health",
        description=(
            "Get the previous synthetic patient health data."
        ),
        function=get_previous_health,
        category="health"
    ),

    "compare_health": ToolDefinition(
        name="compare_health",
        description=(
            "Compare current and previous health data."
        ),
        function=compare_health,
        category="health"
    ),

    "what_matters_now": ToolDefinition(
        name="what_matters_now",
        description=(
            "Identify the currently detected health changes."
        ),
        function=get_what_matters_now,
        category="analysis"
    ),

    "current_symptoms": ToolDefinition(
        name="current_symptoms",
        description=(
            "Get the current synthetic patient symptoms."
        ),
        function=get_current_symptoms,
        category="symptoms"
    ),

    "previous_symptoms": ToolDefinition(
        name="previous_symptoms",
        description=(
            "Get the previous synthetic patient symptoms."
        ),
        function=get_previous_symptoms,
        category="symptoms"
    ),

    "compare_symptoms": ToolDefinition(
        name="compare_symptoms",
        description=(
            "Compare current and previous symptoms."
        ),
        function=compare_symptoms,
        category="symptoms"
    ),

    "context_analysis": ToolDefinition(
        name="context_analysis",
        description=(
            "Analyze the available healthcare context."
        ),
        function=analyze_context,
        category="context"
    ),

    "health_snapshot": ToolDefinition(
        name="health_snapshot",
        description=(
            "Return a consolidated health snapshot."
        ),
        function=get_health_snapshot,
        category="snapshot"
    ),

    "decision_snapshot": ToolDefinition(
        name="decision_snapshot",
        description=(
            "Return the current decision-support snapshot."
        ),
        function=get_decision_snapshot,
        category="decision"
    ),

    "change_summary": ToolDefinition(
        name="change_summary",
        description=(
            "Summarize detected changes."
        ),
        function=get_change_summary,
        category="analysis"
    ),

    "knowledge_retrieval": ToolDefinition(
        name="knowledge_retrieval",
        description=(
            "Search the project's knowledge base "
            "for information relevant to a query."
        ),
        function=retrieve_context,
        category="knowledge"
    )
}


# ============================================================
# REGISTRY FUNCTIONS
# ============================================================

def list_tools():
    """
    Return all registered tools.
    """
    return list(TOOLS.values())


def get_tool(name: str) -> ToolDefinition:
    """
    Get one tool by name.
    """
    if name not in TOOLS:
        raise KeyError(
            f"Unknown tool: {name}"
        )

    return TOOLS[name]


def execute_tool(
    name: str,
    *args,
    **kwargs
) -> Any:
    """
    Execute a registered tool.
    """

    tool = get_tool(name)

    if not tool.read_only:
        raise PermissionError(
            f"Tool '{name}' is not approved "
            "for automatic execution."
        )

    return tool.function(
        *args,
        **kwargs
    )


# ============================================================
# REGISTRY SUMMARY
# ============================================================

def registry_summary():
    tools = list_tools()

    categories = {}

    for tool in tools:

        categories.setdefault(
            tool.category,
            []
        )

        categories[
            tool.category
        ].append(
            tool.name
        )

    return {
        "total_tools": len(tools),
        "read_only_tools": sum(
            1
            for tool in tools
            if tool.read_only
        ),
        "categories": categories
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n========== TOOL REGISTRY ==========\n"
    )

    summary = registry_summary()

    print(
        "Total tools:",
        summary["total_tools"]
    )

    print(
        "Read-only tools:",
        summary["read_only_tools"]
    )

    print(
        "\nCategories:"
    )

    for category, tools in (
        summary["categories"].items()
    ):
        print(
            f"- {category}:"
        )

        for tool in tools:
            print(
                f"  • {tool}"
            )

    print(
        "\nAvailable tools:"
    )

    for tool in list_tools():
        print(
            f"- {tool.name}: "
            f"{tool.description}"
        )

    print(
        "\nRegistry status: READY"
    )