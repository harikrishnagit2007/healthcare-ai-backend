def get_current_health():
    return {
        "heart_rate": 96,
        "temperature": 37.8,
        "recorded_at": "2026-09-15"
    }


if __name__ == "__main__":
    health = get_current_health()

    print("Current Health Data:")
    print(health)
