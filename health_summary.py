from health_data import get_current_health
from health_data import get_previous_health

from symptom_data import get_current_symptoms
from symptom_data import get_previous_symptoms

from compare import compare_health
from compare import compare_symptoms

from what_matters_now import get_what_matters_now

from retrieve import retrieve_knowledge

from medication_data import get_medication_data
from reminder_engine import get_all_reminders

from grounding import build_grounded_context

from safety_engine import build_safety_status


def get_health_summary():

    current_health = get_current_health()
    previous_health = get_previous_health()

    current_symptoms = get_current_symptoms()
    previous_symptoms = get_previous_symptoms()

    health_changes = compare_health()
    symptom_changes = compare_symptoms()

    what_matters_now = get_what_matters_now()

    medications = get_medication_data()
    reminders = get_all_reminders()

    knowledge = retrieve_knowledge(
        "current health changes symptoms medications previous health"
    )

    tool_results = {
        "current_health": current_health,
        "previous_health": previous_health,
        "current_symptoms": current_symptoms,
        "previous_symptoms": previous_symptoms,
        "health_changes": health_changes,
        "symptom_changes": symptom_changes,
        "what_matters_now": what_matters_now,
        "medications": medications,
        "reminders": reminders
    }

    grounded_context = build_grounded_context(
        "Provide a context-aware healthcare summary.",
        tool_results,
        knowledge
    )

    safety = build_safety_status(
        tool_results
    )

    return {
        "status": "ok",

        "context_engine": {
            "current_health": current_health,
            "previous_health": previous_health,
            "current_symptoms": current_symptoms,
            "previous_symptoms": previous_symptoms,
            "health_changes": health_changes,
            "symptom_changes": symptom_changes,
            "what_matters_now": what_matters_now,
            "medications": medications,
            "reminders": reminders,
            "retrieved_knowledge": knowledge
        },

        "grounded_context": grounded_context,

        "safety": safety
    }