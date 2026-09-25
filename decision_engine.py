from patient_context import build_patient_context


def decide_what_to_do():
    context = build_patient_context()

    what_matters = context["what_matters_now"]
    symptoms = context["symptoms"]

    meaningful_change = what_matters["status"] == "Meaningful changes detected"
    active_symptoms = [
        name for name, present in symptoms.items()
        if present
    ]

    if meaningful_change and active_symptoms:
        priority = "HIGH"
        action = "Review the changes together with the reported symptoms."

    elif meaningful_change:
        priority = "MEDIUM"
        action = "Review the changes and continue monitoring."

    elif active_symptoms:
        priority = "MEDIUM"
        action = "Review the reported symptoms."

    else:
        priority = "LOW"
        action = "No major change detected."

    return {
        "priority": priority,
        "action": action,
        "meaningful_change": meaningful_change,
        "active_symptoms": active_symptoms
    }


if __name__ == "__main__":
    decision = decide_what_to_do()

    print("========== DECISION ENGINE ==========")
    print("Priority:", decision["priority"])
    print("Action:", decision["action"])
    print("Meaningful Change:", decision["meaningful_change"])
    print("Active Symptoms:", decision["active_symptoms"])