import json


SAFETY_RULES = {
    "no_diagnosis": True,
    "no_prescribing": True,
    "no_dosage_changes": True,
    "no_unsupported_relationships": True,
    "ocr_requires_verification": True,
    "synthetic_data_requires_label": True,
    "human_review_supported": True
}


def build_safety_status(context):

    review_required = False
    review_reasons = []

    if SAFETY_RULES["synthetic_data_requires_label"]:
        review_required = True
        review_reasons.append(
            "Current development data is synthetic or de-identified."
        )

    if SAFETY_RULES["human_review_supported"]:
        review_reasons.append(
            "Clinical decisions should remain under appropriate human supervision."
        )

    if not context:
        review_required = True
        review_reasons.append(
            "No context was supplied."
        )

    return {
        "safety_status": "review_required" if review_required else "safe_to_display",
        "review_required": review_required,
        "rules": SAFETY_RULES,
        "review_reasons": review_reasons
    }


def build_safe_response(raw_response, context):

    safety = build_safety_status(context)

    return {
        "response": raw_response,
        "safety": safety,
        "disclaimer": (
            "This system provides informational decision support only. "
            "It does not diagnose diseases, prescribe medicines, "
            "or recommend dosage changes."
        )
    }


def get_safety_rules():

    return {
        "status": "active",
        "rules": SAFETY_RULES
    }


if __name__ == "__main__":

    test_context = {
        "synthetic_data": True,
        "health_changes": {},
        "what_matters_now": {}
    }

    result = build_safety_status(test_context)

    print("\n========== SAFETY ENGINE ==========\n")
    print(json.dumps(result, indent=4))