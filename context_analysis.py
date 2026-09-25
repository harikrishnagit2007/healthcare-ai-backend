from patient_context import build_patient_context


def analyze_context():
    context = build_patient_context()

    return {
        "current_health": context["current_health"],
        "previous_health": context["previous_health"],
        "symptoms": context["symptoms"],
        "comparison": context["comparison"],
        "what_matters_now": context["what_matters_now"]
    }


if __name__ == "__main__":
    result = analyze_context()

    print("========== CONTEXT ANALYSIS ==========")
    print(result)