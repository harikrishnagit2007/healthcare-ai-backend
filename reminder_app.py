import json
import time
import tkinter as tk
from datetime import datetime, timedelta
from threading import Thread
import winsound

from reminder_engine import get_all_reminders

STATUS_FILE = "reminder_status.json"
TEST_MODE = False

runtime_status = {}
snooze_times = {}


def load_status():
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_status():
    with open(
        STATUS_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(runtime_status, file, indent=2)


def reminder_key(reminder):
    return (
        reminder["date"]
        + "|"
        + reminder["medicine_name"]
        + "|"
        + reminder["reminder_time"]
    )


def play_alert():
    for _ in range(5):
        winsound.Beep(1000, 500)
        time.sleep(0.2)


def show_reminder(root, reminder):
    key = reminder_key(reminder)

    if runtime_status.get(key) in ["taken", "skipped"]:
        return

    popup = tk.Toplevel(root)
    popup.title("Healthcare Reminder")
    popup.geometry("500x320")
    popup.resizable(False, False)
    popup.attributes("-topmost", True)

    title = tk.Label(
        popup,
        text="Medication Reminder",
        font=("Arial", 22, "bold")
    )
    title.pack(pady=25)

    medicine = tk.Label(
        popup,
        text=reminder["medicine_name"],
        font=("Arial", 20)
    )
    medicine.pack(pady=5)

    scheduled = tk.Label(
        popup,
        text="Scheduled time: " + reminder["reminder_time"],
        font=("Arial", 13)
    )
    scheduled.pack(pady=5)

    status_label = tk.Label(
        popup,
        text="Status: pending",
        font=("Arial", 12)
    )
    status_label.pack(pady=5)

    button_frame = tk.Frame(popup)
    button_frame.pack(pady=25)

    def finish(status_text):
        runtime_status[key] = status_text
        save_status()

        status_label.config(
            text="Status: " + status_text
        )

        taken_button.config(state="disabled")
        skip_button.config(state="disabled")
        snooze_button.config(state="disabled")

    def mark_taken():
        finish("taken")

    def mark_skipped():
        finish("skipped")

    def mark_snoozed():
        snooze_times[key] = datetime.now() + timedelta(minutes=10)
        finish("snoozed")

    taken_button = tk.Button(
        button_frame,
        text="Taken",
        width=12,
        height=2,
        command=mark_taken
    )
    taken_button.grid(row=0, column=0, padx=5)

    skip_button = tk.Button(
        button_frame,
        text="Skip",
        width=12,
        height=2,
        command=mark_skipped
    )
    skip_button.grid(row=0, column=1, padx=5)

    snooze_button = tk.Button(
        button_frame,
        text="Snooze 10m",
        width=12,
        height=2,
        command=mark_snoozed
    )
    snooze_button.grid(row=0, column=2, padx=5)

    popup.lift()
    popup.focus_force()

    Thread(
        target=play_alert,
        daemon=True
    ).start()


def test_reminder(root):
    reminders = get_all_reminders()

    if not reminders:
        print("\nNo medication reminders found.")
        return

    test_reminder_data = reminders[0]

    print("\nTEST MODE: Showing saved medication reminder now...\n")
    print(test_reminder_data)

    show_reminder(root, test_reminder_data)


def check_reminders(root):
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    for reminder in get_all_reminders():
        key = reminder_key(reminder)

        if runtime_status.get(key) in ["taken", "skipped"]:
            continue

        snooze_time = snooze_times.get(key)

        if snooze_time is not None:
            if now >= snooze_time:
                show_reminder(root, reminder)
                snooze_times.pop(key, None)

            continue

        if (
            reminder["date"] == current_date
            and reminder["reminder_time"] == current_time
        ):
            show_reminder(root, reminder)

    root.after(
        20000,
        lambda: check_reminders(root)
    )


runtime_status = load_status()

root = tk.Tk()
root.withdraw()

print("\n========== HEALTHCARE REMINDER APP ==========\n")
print("Reminder system is running.")

if TEST_MODE:
    print("TEST MODE is ON.")
    root.after(
        500,
        lambda: test_reminder(root)
    )
    print(
        "\nAfter testing, change TEST_MODE = False "
        "for real scheduled reminders."
    )
else:
    print("REAL SCHEDULE MODE is ON.")
    print("Scheduled times: 09:00 and 21:00")
    print("Keep this program running.")
    print("Press Ctrl+C to stop.\n")

    root.after(
        1000,
        lambda: check_reminders(root)
    )

try:
    root.mainloop()
except KeyboardInterrupt:
    print("\nReminder app stopped.")