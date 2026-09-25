import json
import os


STATUS_FILE = "reminder_status.json"


def load_statuses():

    if not os.path.exists(STATUS_FILE):
        return {}

    try:

        with open(
            STATUS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        normalized = {}

        for key, value in data.items():

            if isinstance(value, str):

                normalized[key] = {
                    "status": value
                }

            elif isinstance(value, dict):

                normalized[key] = value

            else:

                normalized[key] = {
                    "status": "pending"
                }

        return normalized

    except Exception:

        return {}


def save_statuses(statuses):

    with open(
        STATUS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            statuses,
            file,
            indent=4
        )


def make_reminder_key(reminder):

    return (
        reminder["date"]
        + "|"
        + reminder["medicine_name"]
        + "|"
        + reminder["reminder_time"]
    )


def save_reminder_status(
    reminder,
    status,
    snooze_minutes=10
):

    statuses = load_statuses()

    key = make_reminder_key(
        reminder
    )

    record = {
        "status": status
    }

    if status == "snoozed":

        record["snooze_minutes"] = snooze_minutes

    statuses[key] = record

    save_statuses(
        statuses
    )

    return {
        "key": key,
        **record
    }