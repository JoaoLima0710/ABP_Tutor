from datetime import date
from typing import Dict, Any, Optional

from abp_tutor.db_app import _get_client
from abp_tutor.config import get_settings
from abp_tutor.logging_setup import logger


def start_run(plan_date: date) -> int:
    """Inicia um registro de log de execução."""
    client = _get_client()
    resp = client.table("tutor_run_log").insert({
        "plan_date": plan_date.isoformat(),
        "status": "running"
    }).execute()
    return resp.data[0]["id"]


def finish_run(run_id: int, status: str, error: str = None, plan_date: date = None) -> None:
    """Finaliza o log de execução."""
    client = _get_client()
    data = {
        "status": status,
        "finished_at": "now()",
    }
    if error:
        data["error_message"] = error
    if plan_date:
        data["plan_date"] = plan_date.isoformat()
        
    client.table("tutor_run_log").update(data).eq("id", run_id).execute()


def get_existing_plan(plan_date: date) -> Optional[Dict[str, Any]]:
    """Busca um plano já existente para a data (idempotência)."""
    client = _get_client()
    resp = client.table("tutor_daily_plan").select("*").eq("plan_date", plan_date.isoformat()).execute()
    if resp.data:
        return resp.data[0]
    return None


def save_daily_plan(plan_date: date, day_plan: Dict[str, Any], tutor_result: Dict[str, Any]) -> int:
    """Salva o plano recém-gerado no Supabase."""
    client = _get_client()
    data = {
        "plan_date": plan_date.isoformat(),
        "day_index": day_plan["day_index"],
        "macro_topic": day_plan["macro_topic"],
        "subtopics": day_plan["subtopics"],
        "text_md": tutor_result["text_md"],
        "flashcards": tutor_result["flashcards"],
        "priority_areas": tutor_result["priority_areas"],
        "nudge": tutor_result["nudge"],
        "questions_target": day_plan["questions_target"],
        "flashcards_target": day_plan["flashcards_target"],
        "text_word_count": len(tutor_result["text_md"].split()),
        "model_used": tutor_result.get("model_used"),
    }
    
    resp = client.table("tutor_daily_plan").insert(data).execute()
    return resp.data[0]["id"]


def mark_delivered(plan_id: int) -> None:
    """Marca o plano como entregue via Telegram."""
    client = _get_client()
    client.table("tutor_daily_plan").update({"delivered_at": "now()"}).eq("id", plan_id).execute()


def get_compliance(plan_date: date) -> Optional[Dict[str, Any]]:
    """Busca aderência de uma data específica."""
    client = _get_client()
    resp = client.table("tutor_daily_compliance").select("*").eq("plan_date", plan_date.isoformat()).execute()
    if resp.data:
        return resp.data[0]
    return None
