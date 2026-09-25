def get_current_symptoms():
    return {
        "dizziness": True,
        "fatigue": False,
        "cough": False
    }


if __name__ == "__main__":
    symptoms = get_current_symptoms()

    print("Current Symptoms:")
    print(symptoms)