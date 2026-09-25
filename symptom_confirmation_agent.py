import json

from symptom_confirmation_service import (
    analyze_symptom_confirmation,
    record_confirmation,
    get_confirmed_symptoms
)


# ============================================================
# NORMALIZE YES / NO
# ============================================================

def normalize_answer(answer):
    """
    Convert different user inputs into True / False.

    Returns:
        True  -> YES
        False -> NO
        None  -> invalid / unclear
    """

    if answer is None:
        return None

    value = str(answer).strip().lower()

    yes_values = {
        "yes",
        "y",
        "yeah",
        "yep",
        "true",
        "1"
    }

    no_values = {
        "no",
        "n",
        "nope",
        "false",
        "0"
    }

    if value in yes_values:
        return True

    if value in no_values:
        return False

    return None


# ============================================================
# GET NEXT QUESTION
# ============================================================

def get_next_confirmation_question():
    """
    Analyze the current symptom state and return
    the next pending Yes/No question.
    """

    result = analyze_symptom_confirmation()

    questions = result.get(
        "confirmation_questions",
        []
    )

    confirmed = set(
        result.get(
            "confirmed_symptoms",
            []
        )
    )

    # --------------------------------------------------------
    # Find a question that has not already been confirmed.
    # --------------------------------------------------------

    for question in questions:

        candidate = question.get(
            "candidate"
        )

        if candidate not in confirmed:

            return {
                "status": "QUESTION_READY",
                "question": question,
                "confirmed_symptoms": list(
                    confirmed
                )
            }

    return {
        "status": "NO_PENDING_CONFIRMATION",
        "question": None,
        "confirmed_symptoms": list(
            confirmed
        )
    }


# ============================================================
# PROCESS USER ANSWER
# ============================================================

def process_confirmation_answer(
    candidate,
    answer
):
    """
    Process a Yes/No answer for one symptom candidate.
    """

    confirmed = normalize_answer(
        answer
    )

    if confirmed is None:

        return {
            "status": "INVALID_ANSWER",
            "message": (
                "Please answer only Yes or No."
            ),
            "candidate": candidate
        }

    record = record_confirmation(
        candidate,
        confirmed
    )

    return {
        "status": "CONFIRMATION_RECORDED",
        "candidate": candidate,
        "confirmed": confirmed,
        "record": record,
        "all_confirmed_symptoms": (
            get_confirmed_symptoms()
        )
    }


# ============================================================
# INTERACTIVE AGENT SESSION
# ============================================================

def run_confirmation_agent():
    """
    Interactive confirmation session.

    The system:
    1. Finds a pending symptom candidate.
    2. Asks Yes/No.
    3. Saves the answer.
    4. Continues to the next candidate.
    """

    print(
        "\n========== SYMPTOM CONFIRMATION AGENT ==========\n"
    )

    while True:

        next_question = (
            get_next_confirmation_question()
        )

        if next_question[
            "status"
        ] == "NO_PENDING_CONFIRMATION":

            print(
                "\nNo pending symptom confirmation."
            )

            print(
                "\nConfirmed symptoms:"
            )

            print(
                next_question[
                    "confirmed_symptoms"
                ]
            )

            break

        question = next_question[
            "question"
        ]

        candidate = question[
            "candidate"
        ]

        question_text = question[
            "question"
        ]

        print(
            "\nAgent:"
        )

        print(
            question_text
            + " (Yes/No)"
        )

        answer = input(
            "\nYou:\n> "
        )

        result = process_confirmation_answer(
            candidate,
            answer
        )

        if result[
            "status"
        ] == "INVALID_ANSWER":

            print(
                "\nAgent:"
            )

            print(
                result["message"]
            )

            continue

        print(
            "\nConfirmation saved:"
        )

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
                default=str
            )
        )

        # ----------------------------------------------------
        # Continue automatically.
        # ----------------------------------------------------

        print(
            "\nChecking for another symptom..."
        )


# ============================================================
# TEST MODE
# ============================================================

if __name__ == "__main__":

    try:

        run_confirmation_agent()

    except KeyboardInterrupt:

        print(
            "\nConfirmation agent stopped."
        )

    except Exception as error:

        print(
            "\n========== ERROR ==========\n"
        )

        print(
            type(error).__name__,
            ":",
            str(error)
        )