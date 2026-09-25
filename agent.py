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
        with open(
            STATUS_FILE,
            "r",
            encoding="utf-8"
        ) as file:
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


question = input(
    "Ask the healthcare agent:\n> "
)

symptom_text = input(
    "\nDescribe any current symptom "
    "(press Enter to skip):\n> "
)

image_path = input(
    "\nSkin image path "
    "(press Enter to skip):\n> "
)

current_health = get_current_health()
previous_health = get_previous_health()
current_symptoms = get_current_symptoms()
previous_symptoms = get_previous_symptoms()

health_changes = compare_health()
symptom_changes = compare_symptoms()
what_matters = get_what_matters_now()

knowledge = retrieve_knowledge(
    question,
    top_k=3
)

symptom_information = (
    None
    if symptom_text.strip() == ""
    else extract_symptom_information(
        symptom_text.strip()
    )
)

skin_result = (
    None
    if image_path.strip() == ""
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

print(
    "\n========== ALL TOOLS CHECKED ==========\n"
)

print("1. Current health data")
print("2. Previous health data")
print("3. Current symptoms")
print("4. Previous symptoms")
print("5. Health comparison")
print("6. Symptom comparison")
print("7. What Matters Now")
print("8. Knowledge retrieval")
print("9. Symptom conversation")
print("10. Grounding")
print(
    "11. Skin image analysis"
    if skin_result
    else
    "11. Skin image analysis (skipped)"
)
print("12. Medication / prescription data")
print("13. Medication reminder schedule")
print("14. Medication reminder history")

grounded_context = grounding_prompt(
    question,
    what_matters,
    knowledge
)

symptom_context = json.dumps(
    symptom_information
    if symptom_information
    else {
        "status": "No symptom description provided"
    },
    indent=2
)

image_context = json.dumps(
    skin_result
    if skin_result
    else {
        "status": "No skin image provided"
    },
    indent=2
)

medication_context = json.dumps(
    medication_information,
    indent=2
)

reminder_context = json.dumps(
    reminders,
    indent=2
)

history_context = json.dumps(
    reminder_history,
    indent=2
)

final_context = (
    grounded_context
    + "\n\nSYMPTOM CONVERSATION:\n"
    + symptom_context
    + "\n\nSKIN IMAGE ANALYSIS:\n"
    + image_context
    + "\n\nMEDICATION / PRESCRIPTION DATA:\n"
    + medication_context
    + "\n\nMEDICATION REMINDER SCHEDULE:\n"
    + reminder_context
    + "\n\nMEDICATION REMINDER HISTORY:\n"
    + history_context
)

print(
    "\n========== GROUNDED CONTEXT ==========\n"
)

print(final_context)

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

print(
    "\n========== HEALTHCARE AGENT RESPONSE ==========\n"
)

print(
    response.choices[0].message.content
)