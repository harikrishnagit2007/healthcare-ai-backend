from huggingface_hub import InferenceClient

from patient_context import build_patient_context
from agent_tools import knowledge_retrieval_tool


client = InferenceClient()


def run_health_agent():

    # 1. Build one complete patient context
    patient_context = build_patient_context()

    current_health = patient_context["current_health"]
    previous_health = patient_context["previous_health"]
    symptoms = patient_context["symptoms"]
    comparison = patient_context["comparison"]
    what_matters_now = patient_context["what_matters_now"]

    # 2. Create a context-rich retrieval query
    retrieval_query = f"""
    Current health:
    {current_health}

    Previous health:
    {previous_health}

    Symptoms:
    {symptoms}

    Comparison:
    {comparison}

    Meaningful changes:
    {what_matters_now["changes"]}
    """

    # 3. Retrieve relevant knowledge
    knowledge = knowledge_retrieval_tool(
        retrieval_query,
        top_k=3
    )

    # 4. Format sources
    sources = []

    for index, item in enumerate(knowledge, start=1):
        sources.append(
            f"Source {index} "
            f"(score: {item['score']:.4f}): "
            f"{item['text']}"
        )

    source_text = "\n\n".join(sources)

    # 5. Display patient context
    print("========== HEALTH AGENT ==========\n")

    print("PATIENT CONTEXT:")
    print(patient_context)

    print("\nRETRIEVED SOURCES:")
    print(source_text)

    # 6. Build grounded prompt
    prompt = f"""
You are a healthcare information assistant.

PATIENT CONTEXT:
{patient_context}

RETRIEVED SOURCES:
{source_text}

Your task is to summarize the recorded changes using the patient
context and retrieved sources.

IMPORTANT RULES:

1. Use only the retrieved sources for medical explanations.
2. Patient data can be described exactly as recorded.
3. Do not diagnose.
4. Do not prescribe medicines.
5. Do not recommend changing medication doses.
6. Do not invent medical facts.
7. Do not assume that a symptom has a specific cause.
8. Clearly separate recorded facts from general explanations.
9. If a claim cannot be supported by the retrieved sources,
say that the available sources are insufficient.
10. Keep the answer simple and clear.
11. Recommend qualified professional review when appropriate.

Return the response in this format:

WHAT MATTERS NOW:
<recorded changes and symptoms>

SUPPORTED EXPLANATION:
<only explanations supported by the retrieved sources>

LIMITATIONS:
<what the available sources do not explain>

NEXT STEP:
<safe general next step>

SOURCES USED:
<source numbers>
"""

    # 7. Generate the response
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    answer = response.choices[0].message.content

    print("\nAI AGENT RESPONSE:")
    print(answer)

    return {
        "patient_context": patient_context,
        "sources": knowledge,
        "answer": answer
    }


if __name__ == "__main__":
    run_health_agent()