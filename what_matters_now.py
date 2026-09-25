from compare import compare_health

def get_what_matters_now(): return {
"status": "Changes detected" if compare_health() else "No changes detected",
"new_symptoms": {
field: change
for field, change in compare_health().items()
if field.startswith("symptoms.")
and change["previous"] is False
and change["current"] is True
},
"changed_vitals": {
field: change
for field, change in compare_health().items()
if field.startswith("vital_signs.")
},
"changed_lifestyle": {
field: change
for field, change in compare_health().items()
if field.startswith("lifestyle.")
},
"other_changes": {
field: change
for field, change in compare_health().items()
if not (
field.startswith("symptoms.")
or field.startswith("vital_signs.")
or field.startswith("lifestyle.")
)
}
}
