def get_previous_symptoms():
    return {
        "dizziness": False,
        "fatigue": False,
        "cough": False
    }


if __name__ == "__main__":
    symptoms = get_previous_symptoms()

    print("Previous Symptoms:")
    print(symptoms)