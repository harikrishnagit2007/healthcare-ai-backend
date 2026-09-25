from health_snapshot import get_health_snapshot
from compare_health import compare_health
from compare_symptoms import compare_symptoms
from what_matters_now import get_what_matters_now


def get_decision_snapshot():
    snapshot = get_health_snapshot()
    health_comparison = compare_health()
    symptom_comparison = compare_symptoms()
    what_matters = get_what_matters_now()

    return {
        "current_health": snapshot["current_health"],
        "symptoms": snapshot["symptoms"],
        "health_comparison": health_comparison,
        "symptom_comparison": symptom_comparison,
        "what_matters_now": what_matters
    }


if __name__ == "__main__":
    result = get_decision_snapshot()

    print("========== DECISION SNAPSHOT ==========")

    print("\nCurrent Health:")
    print(result["current_health"])

    print("\nCurrent Symptoms:")
    print(result["symptoms"])

    print("\nHealth Comparison:")
    print(result["health_comparison"])

    print("\nSymptom Comparison:")
    print(result["symptom_comparison"])

    print("\nWhat Matters Now:")
    print(result["what_matters_now"])