def build_doctor_review(summary):

    context = summary.get("context_engine", {})
    safety = summary.get("safety", {})

    current_health = context.get("current_health", {})
    previous_health = context.get("previous_health", {})
    health_changes = context.get("health_changes", {})
    symptom_changes = context.get("symptom_changes", {})
    what_matters_now = context.get("what_matters_now", {})
    medications = context.get("medications", {})
    reminders = context.get("reminders", [])

    review_flags = []

    if health_changes:
        review_flags.append(
            "Health data changes are available for professional review."
        )

    if symptom_changes:
        review_flags.append(
            "Symptom changes are available for professional review."
        )

    if safety.get("review_required"):
        review_flags.append(
            "Safety review is required before clinical interpretation."
        )

    return {
        "review_status": "doctor_review_ready",

        "patient_context": {
            "current_health": current_health,
            "previous_health": previous_health
        },

        "changes_for_review": {
            "health_changes": health_changes,
            "symptom_changes": symptom_changes
        },

        "what_matters_now": what_matters_now,

        "medication_context": {
            "medications": medications,
            "reminders": reminders
        },

        "safety": safety,

        "review_flags": review_flags,

        "ai_role": {
            "diagnosis": False,
            "prescribing": False,
            "dosage_changes": False,
            "clinical_decision": False,
            "human_review": True
        },

        "reviewer_note": (
            "This packet is intended to organize recorded information "
            "for human review. It does not provide a diagnosis, "
            "prescription, or dosage change."
        )
    }


def get_doctor_review(summary):

    return build_doctor_review(summary)