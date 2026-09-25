from __future__ import annotations

from typing import Any


SUPPORTED_LANGUAGES = {
    "en": "English",
    "ta": "Tamil",
    "hi": "Hindi",
    "te": "Telugu",
    "ml": "Malayalam",
}


LANGUAGE_INSTRUCTIONS = {
    "en": (
        "Respond in clear, simple English. "
        "Keep medical terminology understandable."
    ),
    "ta": (
        "Respond in clear, simple Tamil. "
        "Keep important medical terms understandable "
        "and provide the English medical term in brackets "
        "when useful."
    ),
    "hi": (
        "Respond in clear, simple Hindi. "
        "Keep important medical terms understandable "
        "and provide the English medical term in brackets "
        "when useful."
    ),
    "te": (
        "Respond in clear, simple Telugu. "
        "Keep important medical terms understandable "
        "and provide the English medical term in brackets "
        "when useful."
    ),
    "ml": (
        "Respond in clear, simple Malayalam. "
        "Keep important medical terms understandable "
        "and provide the English medical term in brackets "
        "when useful."
    ),
}


COMMON_TRANSLATIONS = {
    "en": {
        "safety_alert": "Safety alert",
        "seek_care": "Please seek medical attention.",
        "not_diagnosis": "This is not a diagnosis.",
        "what_matters_now": "What Matters Now?",
        "current_symptoms": "Current Symptoms",
        "medication": "Medication",
        "doctor_summary": "Doctor Summary",
        "yes": "Yes",
        "no": "No",
        "not_sure": "Not Sure",
    },

    "ta": {
        "safety_alert": "பாதுகாப்பு எச்சரிக்கை",
        "seek_care": "தயவுசெய்து மருத்துவ உதவியை நாடுங்கள்.",
        "not_diagnosis": "இது ஒரு நோயறிதல் அல்ல.",
        "what_matters_now": "இப்போது முக்கியமானது என்ன?",
        "current_symptoms": "தற்போதைய அறிகுறிகள்",
        "medication": "மருந்து",
        "doctor_summary": "மருத்துவர் சுருக்கம்",
        "yes": "ஆம்",
        "no": "இல்லை",
        "not_sure": "உறுதியாக தெரியவில்லை",
    },

    "hi": {
        "safety_alert": "सुरक्षा चेतावनी",
        "seek_care": "कृपया चिकित्सा सहायता लें।",
        "not_diagnosis": "यह कोई निदान नहीं है।",
        "what_matters_now": "अभी क्या महत्वपूर्ण है?",
        "current_symptoms": "वर्तमान लक्षण",
        "medication": "दवा",
        "doctor_summary": "डॉक्टर सारांश",
        "yes": "हाँ",
        "no": "नहीं",
        "not_sure": "पक्का नहीं",
    },

    "te": {
        "safety_alert": "భద్రతా హెచ్చరిక",
        "seek_care": "దయచేసి వైద్య సహాయం పొందండి.",
        "not_diagnosis": "ఇది రోగ నిర్ధారణ కాదు.",
        "what_matters_now": "ఇప్పుడు ముఖ్యమైనది ఏమిటి?",
        "current_symptoms": "ప్రస్తుత లక్షణాలు",
        "medication": "మందు",
        "doctor_summary": "డాక్టర్ సారాంశం",
        "yes": "అవును",
        "no": "లేదు",
        "not_sure": "ఖచ్చితంగా తెలియదు",
    },

    "ml": {
        "safety_alert": "സുരക്ഷാ മുന്നറിയിപ്പ്",
        "seek_care": "ദയവായി വൈദ്യസഹായം തേടുക.",
        "not_diagnosis": "ഇത് ഒരു രോഗനിർണയം അല്ല.",
        "what_matters_now": "ഇപ്പോൾ പ്രധാനപ്പെട്ടത് എന്താണ്?",
        "current_symptoms": "നിലവിലെ ലക്ഷണങ്ങൾ",
        "medication": "മരുന്ന്",
        "doctor_summary": "ഡോക്ടർ സംഗ്രഹം",
        "yes": "അതെ",
        "no": "ഇല്ല",
        "not_sure": "ഉറപ്പില്ല",
    },
}


def normalize_language(language: str | None) -> str:
    if not language:
        return "en"

    language = language.lower().strip()

    aliases = {
        "english": "en",
        "tamil": "ta",
        "தமிழ்": "ta",
        "hindi": "hi",
        "हिन्दी": "hi",
        "telugu": "te",
        "తెలుగు": "te",
        "malayalam": "ml",
        "മലയാളം": "ml",
    }

    return aliases.get(
        language,
        language if language in SUPPORTED_LANGUAGES else "en",
    )


def get_language_info(
    language: str | None = None,
) -> dict[str, str]:

    code = normalize_language(language)

    return {
        "code": code,
        "name": SUPPORTED_LANGUAGES[code],
        "instruction": LANGUAGE_INSTRUCTIONS[code],
    }


def get_text(
    key: str,
    language: str | None = None,
) -> str:

    code = normalize_language(language)

    return (
        COMMON_TRANSLATIONS
        .get(code, COMMON_TRANSLATIONS["en"])
        .get(key, COMMON_TRANSLATIONS["en"].get(key, key))
    )


def build_response_instruction(
    language: str | None = None,
) -> str:

    code = normalize_language(language)

    return LANGUAGE_INSTRUCTIONS[code]


def localize_system_message(
    message_type: str,
    language: str | None = None,
) -> str:

    code = normalize_language(language)

    translations = COMMON_TRANSLATIONS.get(
        code,
        COMMON_TRANSLATIONS["en"],
    )

    return translations.get(
        message_type,
        COMMON_TRANSLATIONS["en"].get(
            message_type,
            message_type,
        ),
    )


def build_multilingual_context(
    language: str | None = None,
) -> dict[str, Any]:

    info = get_language_info(language)

    return {
        "language": info["code"],
        "language_name": info["name"],
        "instruction": info["instruction"],
        "supported_languages": SUPPORTED_LANGUAGES,
    }


def run_local_test() -> None:

    print()
    print("=" * 55)
    print("MULTILINGUAL HEALTH SERVICE TEST")
    print("=" * 55)

    for code, name in SUPPORTED_LANGUAGES.items():

        print()
        print(f"{name} ({code})")

        print(
            "  What Matters Now:",
            get_text(
                "what_matters_now",
                code,
            ),
        )

        print(
            "  Safety:",
            get_text(
                "safety_alert",
                code,
            ),
        )

        print(
            "  Doctor:",
            get_text(
                "doctor_summary",
                code,
            ),
        )

    print()
    print("Multilingual service test completed.")


if __name__ == "__main__":
    run_local_test()