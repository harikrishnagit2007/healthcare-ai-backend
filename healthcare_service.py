import json
from huggingface_hub import InferenceClient

from health_data import get_current_health
from health_data import get_previous_health
from symptom_data import get_current_symptoms
from symptom_data import get_previous_symptoms
from compare import compare_health
from compare import compare_symptoms
from what_matters_now import get_what_matters_now
from retrieve import retrieve_knowledge
from grounding import grounding_prompt
from skin_analysis import analyze_skin_image
from syptom_conversation import extract_symptom_information
from medication_data import get_medication_data
from reminder_engine import get_all_reminders

MODEL = "openai/gpt-oss-120b"
STATUS_FILE = "reminder_status.json"

client = InferenceClient()


def load_reminder_status():
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def reminder_key(reminder):
    return (
        reminder["date"]
        + "|"
        + reminder["medicine_name"]
        + "|"
        + reminder["reminder_time"]
    )


def build_reminder_history(reminders, saved_status):
    return [
        {
            **reminder,
            "status": saved_status.get(
                reminder_key(reminder),
                "pending"
            )
        }
        for reminder in reminders
    ]


def process_healthcare(
    question,
    symptom_text="",
    image_path=""
):
    get_current_health()
    get_previous_health()
    get_current_symptoms()
    get_previous_symptoms()

    health_changes = compare_health()
    symptom_changes = compare_symptoms()

    what_matters = get_what_matters_now()

    knowledge = retrieve_knowledge(
        question,
        top_k=3
    )

    symptom_information = (
        None
        if not symptom_text.strip()
        else extract_symptom_information(
            symptom_text.strip()
        )
    )

    skin_result = (
        None
        if not image_path.strip()
        else analyze_skin_image(
            image_path.strip()
        )
    )

    medication_information = get_medication_data()

    reminders = get_all_reminders()

    saved_status = load_reminder_status()

    reminder_history = build_reminder_history(
        reminders,
        saved_status
    )

    grounded_context = grounding_prompt(
        question,
        what_matters,
        knowledge
    )

    final_context = (
        grounded_context
        + "\n\nSYMPTOM CONVERSATION:\n"
        + json.dumps(
            symptom_information
            if symptom_information
            else {
                "status": "No symptom description provided"
            },
            indent=2
        )
        + "\n\nSKIN IMAGE ANALYSIS:\n"
        + json.dumps(
            skin_result
            if skin_result
            else {
                "status": "No skin image provided"
            },
            indent=2
        )
        + "\n\nMEDICATION / PRESCRIPTION DATA:\n"
        + json.dumps(
            medication_information,
            indent=2
        )
        + "\n\nMEDICATION REMINDER SCHEDULE:\n"
        + json.dumps(
            reminders,
            indent=2
        )
        + "\n\nMEDICATION REMINDER HISTORY:\n"
        + json.dumps(
            reminder_history,
            indent=2
        )
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a healthcare information assistant "
                    "for an educational prototype. "
                    "Use only the supplied context. "
                    "Do not invent medical facts. "
                    "Do not diagnose diseases. "
                    "Do not infer causes, relationships, severity, "
                    "or medical meaning that is not explicitly stated. "
                    "Do not combine separate findings to create "
                    "a new medical conclusion. "
                    "Do not prescribe medicines or change medication "
                    "instructions. "
                    "Report medication and reminder information "
                    "exactly as supplied. "
                    "Do not judge adherence or make medical conclusions "
                    "from reminder history. "
                    "Skin-image results are AI classification/reference "
                    "results, not confirmed diagnoses. "
                    "Clearly state that patient data is synthetic test data. "
                    "When information is missing, say it is not available."
                )
            },
            {
                "role": "user",
                "content": final_context
            }
        ]
    )

    return {
        "question": question,
        "health_changes": health_changes,
        "symptom_changes": symptom_changes,
        "what_matters_now": what_matters,
        "knowledge": knowledge,
        "symptom_information": symptom_information,
        "skin_analysis": skin_result,
        "medication": medication_information,
        "reminders": reminders,
        "reminder_history": reminder_history,
        "response": response.choices[0].message.content
    }