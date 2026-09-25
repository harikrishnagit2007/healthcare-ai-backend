from compare_health import compare_health
from compare_symptoms import compare_symptoms


def get_change_summary():
    health = compare_health()
    symptoms = compare_symptoms()

    return {
        "health_changes": {
            "heart_rate_change": health["heart_rate_change"],
            "temperature_change": health["temperature_change"]
        },
        "symptom_changes": symptoms["changes"]
    }


if __name__ == "__main__":
    result = get_change_summary()

    print("========== CHANGE SUMMARY ==========")

    print("\nHealth Changes:")
    print(result["health_changes"])

    print("\nSymptom Changes:")
    print(result["symptom_changes"])