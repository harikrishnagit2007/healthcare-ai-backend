from datetime import datetime, timedelta

from medication_data import get_medication_data

from reminder_store import load_statuses
from reminder_store import save_reminder_status
from reminder_store import make_reminder_key


def get_active_medications():

    return [
        medicine
        for medicine in get_medication_data()["medications"]
        if medicine["status"] == "active"
    ]


def get_reminder_schedule(medicine):

    return [
        {
            "date": (
                datetime.strptime(
                    medicine["start_date"],
                    "%Y-%m-%d"
                )
                + timedelta(days=day)
            ).strftime("%Y-%m-%d"),

            "medicine_name": medicine["medicine_name"],

            "reminder_time": reminder_time,

            "status": "pending"
        }

        for day in range(
            medicine["duration_days"]
        )

        for reminder_time in medicine["reminder_times"]
    ]


def get_all_reminders():

    statuses = load_statuses()

    reminders = []

    for medicine in get_active_medications():

        schedule = get_reminder_schedule(
            medicine
        )

        for reminder in schedule:

            key = make_reminder_key(
                reminder
            )

            saved = statuses.get(
                key,
                {}
            )

            reminders.append(
                {
                    **reminder,

                    "status": saved.get(
                        "status",
                        "pending"
                    ),

                    "snooze_minutes": saved.get(
                        "snooze_minutes",
                        None
                    )
                }
            )

    return reminders


def get_reminders_for_date(
    target_date
):

    return [
        reminder
        for reminder in get_all_reminders()
        if reminder["date"] == target_date
    ]


def update_reminder_status(
    reminder,
    new_status,
    snooze_minutes=10
):

    allowed_statuses = [
        "pending",
        "taken",
        "skipped",
        "snoozed"
    ]

    if new_status not in allowed_statuses:

        return {
            "status": "invalid",
            "message": "Invalid reminder status."
        }

    saved = save_reminder_status(
        reminder,
        new_status,
        snooze_minutes
    )

    return {
        "status": "updated",
        "reminder": reminder,
        "saved": saved
    }