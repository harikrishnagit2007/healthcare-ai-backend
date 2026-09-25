from health_tools import get_current_health
from previous_health import get_previous_health
from compare_health import compare_health
from retrieve_context import retrieve_context
from what_matters_now import get_what_matters_now

from symptom_tools import get_current_symptoms
from previous_symptoms import get_previous_symptoms
from compare_symptoms import compare_symptoms

from context_analysis import analyze_context
from health_snapshot import get_health_snapshot
from decision_snapshot import get_decision_snapshot
from change_summary import get_change_summary


def run_check(name, function, *args, **kwargs):
    print(f"\n[CHECK] {name}")

    try:
        result = function(*args, **kwargs)

        print("STATUS: WORKING")
        print("TYPE:", type(result).__name__)

        if result is None:
            print("RESULT: None")
        elif isinstance(result, (dict, list)):
            print("RESULT: OK")
        else:
            print("RESULT:", str(result)[:300])

        return True

    except Exception as error:
        print("STATUS: FAILED")
        print("ERROR:", type(error).__name__)
        print("MESSAGE:", str(error))

        return False


def main():

    print("\n========== HEALTHCARE TOOL HEALTH CHECK ==========\n")

    results = {}

    results["current_health"] = run_check(
        "Current Health",
        get_current_health
    )

    results["previous_health"] = run_check(
        "Previous Health",
        get_previous_health
    )

    results["compare_health"] = run_check(
        "Health Comparison",
        compare_health
    )

    results["what_matters_now"] = run_check(
        "What Matters Now",
        get_what_matters_now
    )

    results["current_symptoms"] = run_check(
        "Current Symptoms",
        get_current_symptoms
    )

    results["previous_symptoms"] = run_check(
        "Previous Symptoms",
        get_previous_symptoms
    )

    results["compare_symptoms"] = run_check(
        "Symptom Comparison",
        compare_symptoms
    )

    results["context_analysis"] = run_check(
        "Context Analysis",
        analyze_context
    )

    results["health_snapshot"] = run_check(
        "Health Snapshot",
        get_health_snapshot
    )

    results["decision_snapshot"] = run_check(
        "Decision Snapshot",
        get_decision_snapshot
    )

    results["change_summary"] = run_check(
        "Change Summary",
        get_change_summary
    )

    print("\n[CHECK] Knowledge Retrieval")

    try:
        knowledge = retrieve_context(
            "health changes",
            top_k=3
        )

        print("STATUS: WORKING")
        print(
            "DOCUMENTS RETURNED:",
            len(knowledge)
        )

        results["knowledge_retrieval"] = True

    except Exception as error:

        print("STATUS: FAILED")
        print(
            "ERROR:",
            type(error).__name__
        )
        print(
            "MESSAGE:",
            str(error)
        )

        results["knowledge_retrieval"] = False

    print(
        "\n========== FINAL TOOL STATUS ==========\n"
    )

    total = len(results)
    working = sum(
        1
        for value in results.values()
        if value
    )
    failed = total - working

    for name, status in results.items():
        print(
            f"{name:25} : "
            + (
                "WORKING"
                if status
                else "FAILED"
            )
        )

    print(
        "\nTotal tools checked:",
        total
    )

    print(
        "Working:",
        working
    )

    print(
        "Failed:",
        failed
    )

    if failed == 0:
        print(
            "\nFINAL STATUS: ALL TOOLS WORKING"
        )
    else:
        print(
            "\nFINAL STATUS: SOME TOOLS FAILED"
        )


if __name__ == "__main__":
    main()