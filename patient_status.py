from patient_context import build_patient_context
from agent_tools import knowledge_retrieval_tool


def analyze_patient_status():
    context = build_patient_context()

    current = context["current_health"]
    previous = context["previous_health"]
    symptoms = context["symptoms"]
    comparison = context["comparison"]
    what_matters = context["what_matters_now"]

    retrieval_query = f"""
    Current health:
    {current}

    Previous health:
    {previous}

    Symptoms:
    {symptoms}

    Changes:
    {what_matters["changes"]}
    """

    knowledge = knowledge_retrieval_tool(
        retrieval_query,
        top_k=3
    )

    return {
        "current_health": current,
        "previous_health": previous,
        "symptoms": symptoms,
        "comparison": comparison,
        "what_matters_now": what_matters,
        "relevant_knowledge": knowledge
    }


if __name__ == "__main__":
    result = analyze_patient_status()

    print("========== PATIENT STATUS ==========")

    print("\nCurrent Health:")
    print(result["current_health"])

    print("\nPrevious Health:")
    print(result["previous_health"])

    print("\nSymptoms:")
    print(result["symptoms"])

    print("\nComparison:")
    print(result["comparison"])

    print("\nWhat Matters Now:")
    print(result["what_matters_now"])

    print("\nRelevant Knowledge:")
    for item in result["relevant_knowledge"]:
        print(
            f"- Score: {item['score']:.4f} | "
            f"{item['text']}"
        )