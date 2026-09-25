from health_tools import get_current_health
from previous_health import get_previous_health
from compare_health import compare_health
from retrieve_context import retrieve_context
from what_matters_now import get_what_matters_now
from symptom_tools import get_current_symptoms
from previous_symptoms import get_previous_symptoms
from compare_symptoms import compare_symptoms
from context_analysis import analyze_context
from health_snapshot import get_health_snapshot
from decision_snapshot import get_decision_snapshot
from change_summary import get_change_summary

def current_health_tool(): return get_current_health()
def previous_health_tool(): return get_previous_health()
def compare_health_tool(): return compare_health()
def what_matters_now_tool(): return get_what_matters_now()
def current_symptoms_tool(): return get_current_symptoms()
def previous_symptoms_tool(): return get_previous_symptoms()
def compare_symptoms_tool(): return compare_symptoms()
def context_analysis_tool(): return analyze_context()
def health_snapshot_tool(): return get_health_snapshot()
def decision_snapshot_tool(): return get_decision_snapshot()
def change_summary_tool(): return get_change_summary()

def knowledge_retrieval_tool(query, top_k=3, min_score=0.25): return [{"text": doc["text"], "score": float(score)} for doc, score in retrieve_context(query, top_k=top_k) if float(score) >= min_score]
