from health_data import get_current_health, get_previous_health
from symptom_data import get_current_symptoms, get_previous_symptoms

flatten = lambda data, prefix="": {
**{
f"{prefix}{key}": value
for key, value in data.items()
if not isinstance(value, dict)
},
**{
nested_key: nested_value
for key, value in data.items()
if isinstance(value, dict)
for nested_key, nested_value in flatten(
value,
f"{prefix}{key}."
).items()
}
}

compare_records = lambda previous, current: {
key: {
"previous": flatten(previous).get(key),
"current": flatten(current).get(key)
}
for key in set(flatten(previous)) | set(flatten(current))
if flatten(previous).get(key) != flatten(current).get(key)
}

compare_health = lambda: {
key: value
for key, value in compare_records(
get_previous_health(),
get_current_health()
).items()
if key != "recorded_at"
}

compare_symptoms = lambda: compare_records(
get_previous_symptoms(),
get_current_symptoms()
)
