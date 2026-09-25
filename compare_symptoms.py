from symptom_tools import get_current_symptoms
from previous_symptoms import get_previous_symptoms


def compare_symptoms():
    current = get_current_symptoms()
    previous = get_previous_symptoms()

    changes = {}

    for symptom in current:
        if current[symptom] != previous.get(symptom):
            changes[symptom] = {
                "previous": previous.get(symptom, False),
                "current": current[symptom],
                "changed": True
            }

    return {
        "current": current,
        "previous": previous,
        "changes": changes
    }


if __name__ == "__main__":
    result = compare_symptoms()

    print("========== SYMPTOM COMPARISON ==========")
    print(result)

    print("\nSymptom Changes:")

    if not result["changes"]:
        print("No symptom changes detected.")
    else:
        for symptom, data in result["changes"].items():
            print(
                f"- {symptom}: "
                f"{data['previous']} -> {data['current']}"
            )