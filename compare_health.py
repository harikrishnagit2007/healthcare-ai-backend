from health_tools import get_current_health
from previous_health import get_previous_health


def compare_health():
    current = get_current_health()
    previous = get_previous_health()

    comparison = {
        "heart_rate_change":
            current["heart_rate"] - previous["heart_rate"],

        "temperature_change":
            current["temperature"] - previous["temperature"],

        "current": current,
        "previous": previous
    }

    return comparison


if __name__ == "__main__":
    result = compare_health()

    print("Health Comparison:")
    print(result)