from health_tools import get_current_health
from symptom_tools import get_current_symptoms


def get_health_snapshot():
    current_health = get_current_health()
    symptoms = get_current_symptoms()

    return {
        "current_health": current_health,
        "symptoms": symptoms
    }


if __name__ == "__main__":
    snapshot = get_health_snapshot()

    print("========== HEALTH SNAPSHOT ==========")
    print(snapshot)