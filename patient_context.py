from health_tools import get_current_health
from previous_health import get_previous_health
from compare_health import compare_health
from symptom_tools import get_current_symptoms
from what_matters_now import get_what_matters_now


def build_patient_context():
    current_health = get_current_health()
    previous_health = get_previous_health()
    comparison = compare_health()
    symptoms = get_current_symptoms()
    what_matters_now = get_what_matters_now()

    return {
        "current_health": current_health,
        "previous_health": previous_health,
        "symptoms": symptoms,
        "comparison": comparison,
        "what_matters_now": what_matters_now
    }


if __name__ == "__main__":
    context = build_patient_context()

    print("========== PATIENT CONTEXT ==========")
    print(context)