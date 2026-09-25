from huggingface_hub import InferenceClient

from patient_context import build_patient_context
from decision_engine import decide_what_to_do
from agent_tools import knowledge_retrieval_tool


client = InferenceClient()


def run_decision_agent():

    # 1. Build patient context
    patient_context = build_patient_context()

    # 2. Run decision engine
    decision = decide_what_to_do()

    # 3. Build retrieval query
    retrieval_query = f"""
    Patient context:
    {patient_context}

    Decision priority:
    {decision["priority"]}

    Decision action:
    {decision["action"]}
    """

    # 4. Retrieve relevant knowledge
    knowledge = knowledge_retrieval_tool(
        retrieval_query,
        top_k=3
    )

    # 5. Format sources
    source_lines = []

    for index, item in enumerate(knowledge, start=1):
        source_lines.append(
            f"Source {index} "
            f"(score: {item['score']:.4f}): "
            f"{item['text']}"
        )

    source_text = "\n\n".join(source_lines)

    # 6. Display decision
    print("========== DECISION AGENT ==========\n")

    print("Priority:", decision["priority"])
    print("Action:", decision["action"])
    print("Active Symptoms:", decision["active_symptoms"])

    print("\nRetrieved Sources:")
    print(source_text)

    # 7. Grounded prompt
    prompt = f"""
You are a healthcare information assistant.

PATIENT CONTEXT:
{patient_context}

DECISION:
Priority: {decision["priority"]}
Action: {decision["action"]}

RETRIEVED SOURCES:
{source_text}

Rules:
- Describe patient data exactly as recorded.
- Use only the retrieved sources for medical explanations.
- Do not diagnose.
- Do not prescribe medicines.
- Do not change medication doses.
- Do not invent medical facts.
- Do not assume a symptom has a specific cause.
- Clearly separate recorded facts from explanations.
- If the sources are insufficient, say so.
- Keep the response simple.
- Recommend qualified professional review when appropriate.

Return:

WHAT MATTERS NOW:
<important recorded changes and symptoms>

WHY:
<only source-supported explanation>

PRIORITY:
<priority and why the system selected it>

NEXT STEP:
<safe general next step>

LIMITATIONS:
<what the sources cannot explain>

SOURCES USED:
<source numbers>
"""

    # 8. Generate AI response
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

    print("\nAI DECISION AGENT RESPONSE:")
    print(answer)


if __name__ == "__main__":
    run_decision_agent()