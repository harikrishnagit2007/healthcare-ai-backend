def build_grounded_context(question, what_matters, knowledge): return {
"user_question": question,
"what_matters_now": {
"status": what_matters.get("status"),
"new_symptoms": what_matters.get("new_symptoms", {}),
"changed_vitals": what_matters.get("changed_vitals", {}),
"changed_lifestyle": what_matters.get("changed_lifestyle", {}),
"other_changes": what_matters.get("other_changes", {})
},
"retrieved_knowledge": knowledge,
"rules": [
"Use only the supplied recorded changes.",
"Use only the supplied retrieved knowledge.",
"Do not invent facts.",
"Do not diagnose diseases.",
"Do not prescribe medicines.",
"Do not claim that two findings are related unless the supplied knowledge explicitly states the relationship.",
"Do not decide a disease stage from symptoms or images.",
"If information is missing, say it is not available.",
"Clearly state that the patient data is synthetic test data."
]
}

def grounding_prompt(question, what_matters, knowledge): return (
"Answer the user's question using ONLY this grounded context.\n\n"
+ str(
build_grounded_context(
question,
what_matters,
knowledge
)
)
+ "\n\n"
+ "Do not add information outside this context."
)
