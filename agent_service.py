import json

from huggingface_hub import InferenceClient

from health_summary import get_health_summary
from doctor_review import get_doctor_review
from safety_engine import build_safety_status
from grounding import grounding_prompt

from syptom_conversation import extract_symptom_information

MODEL = "openai/gpt-oss-120b"

client = InferenceClient()


def run_healthcare_agent(question, symptom_text=""):

    print("\n========== HEALTHCARE AI AGENT ==========\n")

    summary = get_health_summary()

    print("Context Engine: checked")

    doctor_review = get_doctor_review(
        summary
    )

    print("Doctor Review Layer: checked")

    safety = build_safety_status(
        summary.get("context_engine", {})
    )

    print("Safety Engine: checked")

    symptom_information = {}

    if symptom_text.strip():

        try:

            symptom_information = extract_symptom_information(
                symptom_text
            )

        except Exception as error:

            symptom_information = {
                "status": "symptom_extraction_error",
                "message": str(error)
            }

    else:

        symptom_information = {
            "status": "no_new_symptom_text"
        }

    print("Symptom Conversation: checked")

    context = {
        "health_summary": summary,
        "doctor_review": doctor_review,
        "safety": safety,
        "symptom_information": symptom_information
    }

    prompt = (
        "You are a healthcare decision-support assistant.\n\n"

        "Answer the user's question using ONLY the supplied context.\n\n"

        "Rules:\n"
        "1. Do not diagnose a disease.\n"
        "2. Do not prescribe medicines.\n"
        "3. Do not recommend dosage changes.\n"
        "4. Do not invent medical facts.\n"
        "5. Do not infer causes or relationships that are not explicitly supported.\n"
        "6. Do not call a finding normal, abnormal, dangerous, or concerning unless that characterization is explicitly supported by the supplied context.\n"
        "7. Clearly separate recorded facts from AI-generated explanation.\n"
        "8. Prescription OCR information is only a candidate extraction and requires verification.\n"
        "9. Synthetic or de-identified data must be identified as such.\n"
        "10. When information is missing, say that it is not available.\n"
        "11. Encourage appropriate human or clinician review when required by the safety context.\n\n"

        "USER QUESTION:\n"
        + question
        + "\n\n"

        "GROUNDING CONTEXT:\n"
        + grounding_prompt(
            question,
            summary.get("context_engine", {}),
            summary.get("context_engine", {}).get(
                "retrieved_knowledge",
                []
            )
        )
        + "\n\n"

        "DOCTOR REVIEW CONTEXT:\n"
        + json.dumps(
            doctor_review,
            indent=2,
            default=str
        )
        + "\n\n"

        "SAFETY CONTEXT:\n"
        + json.dumps(
            safety,
            indent=2,
            default=str
        )
        + "\n\n"

        "SYMPTOM INFORMATION:\n"
        + json.dumps(
            symptom_information,
            indent=2,
            default=str
        )
    )

    try:

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a grounded healthcare decision-support assistant. "
                        "Follow the safety rules exactly."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        answer = response.choices[0].message.content

    except Exception as error:

        return {
            "status": "error",
            "message": str(error),
            "safety": safety,
            "context": context
        }

    return {
        "status": "ok",
        "question": question,
        "answer": answer,
        "symptom_information": symptom_information,
        "doctor_review": doctor_review,
        "safety": safety,
        "context_engine": summary.get(
            "context_engine",
            {}
        )
    }