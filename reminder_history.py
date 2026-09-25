import json
from reminder_engine import get_all_reminders

STATUS_FILE = "reminder_status.json"


def load_status():
    try:
        with open(
            STATUS_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def build_history():
    saved_status = load_status()
    reminders = get_reminders()

    return [
        {
            **reminder,
            "status": saved_status.get(
                reminder_key(reminder),
                "pending"
            )
        }
        for reminder in reminders
    ]


def reminder_key(reminder):
    return (
        reminder["date"]
        + "|"
        + reminder["medicine_name"]
        + "|"
        + reminder["reminder_time"]
    )


history = build_history()

print("\n========== REMINDER HISTORY ==========\n")

for item in history:
    print(
        item["date"],
        "|",
        item["reminder_time"],
        "|",
        item["medicine_name"],
        "|",
        item["status"]
    )

print("\n========== SUMMARY ==========\n")

print(
    "Total:",
    len(history)
)

print(
    "Taken:",
    len([
        item
        for item in history
        if item["status"] == "taken"
    ])
)

print(
    "Skipped:",
    len([
        item
        for item in history
        if item["status"] == "skipped"
    ])
)

print(
    "Snoozed:",
    len([
        item
        for item in history
        if item["status"] == "snoozed"
    ])
)

print(
    "Pending:",
    len([
        item
        for item in history
        if item["status"] == "pending"
    ])
)