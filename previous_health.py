def get_previous_health():
    return {
        "heart_rate": 78,
        "temperature": 37.1,
        "recorded_at": "2026-09-08"
    }


if __name__ == "__main__":
    health = get_previous_health()

    print("Previous Health Data:")
    print(health)