def get_current_health(): return {
"patient": {"patient_id": "TEST001", "age": 25, "sex": "not_specified"},
"symptoms": {"dizziness": True, "fatigue": False, "cough": False, "skin_issue": True, "chest_discomfort": False},
"vital_signs": {"heart_rate": 96, "blood_pressure": "125/82", "temperature": 37.8, "respiratory_rate": 18, "oxygen_saturation": 97, "height_cm": 170, "weight_kg": 64.5, "bmi": 22.3},
"medical_history": {"conditions": [], "previous_illnesses": [], "surgeries": [], "family_history": []},
"allergies": {"drug_allergies": [], "other_allergies": []},
"medications": {"current": []},
"laboratory_results": {"blood_tests": [], "urine_tests": [], "other_tests": []},
"imaging": {"xray": [], "ct": [], "mri": [], "ultrasound": [], "other": []},
"doctor_visits": {"recent": []},
"immunizations": {"records": []},
"devices": {"wearables": [], "home_monitors": []},
"lifestyle": {"sleep_hours": 6, "activity_level": "moderate"},
"recorded_at": "2026-09-16"
}

def get_previous_health(): return {
"patient": {"patient_id": "TEST001", "age": 25, "sex": "not_specified"},
"symptoms": {"dizziness": False, "fatigue": False, "cough": False, "skin_issue": False, "chest_discomfort": False},
"vital_signs": {"heart_rate": 78, "blood_pressure": "120/80", "temperature": 37.1, "respiratory_rate": 16, "oxygen_saturation": 98, "height_cm": 170, "weight_kg": 65.0, "bmi": 22.5},
"medical_history": {"conditions": [], "previous_illnesses": [], "surgeries": [], "family_history": []},
"allergies": {"drug_allergies": [], "other_allergies": []},
"medications": {"current": []},
"laboratory_results": {"blood_tests": [], "urine_tests": [], "other_tests": []},
"imaging": {"xray": [], "ct": [], "mri": [], "ultrasound": [], "other": []},
"doctor_visits": {"recent": []},
"immunizations": {"records": []},
"devices": {"wearables": [], "home_monitors": []},
"lifestyle": {"sleep_hours": 7, "activity_level": "moderate"},
"recorded_at": "2026-09-09"
}
