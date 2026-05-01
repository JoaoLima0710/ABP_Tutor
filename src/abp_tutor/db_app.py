from datetime import date
from typing import TypedDict, List

from supabase import create_client, Client

from abp_tutor.config import get_settings
from abp_tutor.logging_setup import logger


class TopicAccuracy(TypedDict):
    topic: str
    attempted: int
    correct: int
    accuracy_pct: float


class WeakArea(TypedDict):
    topic: str
    subtopic: str | None
    accuracy_pct: float
    n_attempts: int


_SUPABASE_CLIENT = None
_USER_ID = None

def _get_client() -> Client:
    global _SUPABASE_CLIENT
    if _SUPABASE_CLIENT is None:
        settings = get_settings()
        _SUPABASE_CLIENT = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    return _SUPABASE_CLIENT


def _get_user_id() -> str:
    global _USER_ID
    if _USER_ID is not None:
        return _USER_ID
        
    settings = get_settings()
    if settings.SUPABASE_USER_ID:
        _USER_ID = settings.SUPABASE_USER_ID
        return _USER_ID
        
    # Auto-discovery
    logger.info("Tentando auto-descobrir user_id no Supabase...")
    client = _get_client()
    resp = client.table("user_progress").select("user_id").limit(1).execute()
    if resp.data:
        _USER_ID = resp.data[0]["user_id"]
        logger.info(f"Auto-discovery encontrou user_id: {_USER_ID}")
        return _USER_ID
        
    raise ValueError("Não foi possível descobrir o SUPABASE_USER_ID. Configure no .env")


def get_accuracy_by_topic(since: date, until: date) -> List[TopicAccuracy]:
    """Retorna a precisão por tema baseada nas simulações concluídas no período."""
    client = _get_client()
    user_id = _get_user_id()
    
    # Busca simulações (idealmente filtrar por data, mas por simplicidade vamos trazer as recentes
    # e filtrar no código, já que é single-user)
    resp = client.table("simulations").select("data").eq("user_id", user_id).execute()
    
    topics_acc = {}
    
    for row in resp.data:
        sim_data = row.get("data", {})
        completed_at_str = sim_data.get("completedAt")
        if not completed_at_str:
            continue
            
        completed_at = date.fromisoformat(completed_at_str[:10])
        if since <= completed_at <= until:
            by_theme = sim_data.get("stats", {}).get("byTheme", {})
            for theme, stats in by_theme.items():
                if theme not in topics_acc:
                    topics_acc[theme] = {"attempted": 0, "correct": 0}
                topics_acc[theme]["attempted"] += stats.get("total", 0)
                topics_acc[theme]["correct"] += stats.get("correct", 0)
                
    result = []
    for topic, acc in topics_acc.items():
        if acc["attempted"] > 0:
            result.append(TopicAccuracy(
                topic=topic,
                attempted=acc["attempted"],
                correct=acc["correct"],
                accuracy_pct=round((acc["correct"] / acc["attempted"]) * 100, 2)
            ))
            
    return sorted(result, key=lambda x: x["accuracy_pct"], reverse=True)


def get_weak_areas(since: date, until: date, top_n: int = 3) -> List[WeakArea]:
    """Retorna as áreas mais fracas. Usa user_progress.trends.weakThemes."""
    client = _get_client()
    user_id = _get_user_id()
    
    resp = client.table("user_progress").select("data").eq("user_id", user_id).execute()
    if not resp.data:
        return []
        
    progress_data = resp.data[0].get("data", {})
    weak_themes = progress_data.get("trends", {}).get("weakThemes", [])
    by_theme = progress_data.get("byTheme", {})
    
    result = []
    for theme in weak_themes[:top_n]:
        stats = by_theme.get(theme, {})
        result.append(WeakArea(
            topic=theme,
            subtopic=None,
            accuracy_pct=stats.get("accuracy", 0.0),
            n_attempts=stats.get("totalAttempts", 0)
        ))
        
    return result


def get_questions_done_yesterday(reference: date) -> int:
    client = _get_client()
    user_id = _get_user_id()
    
    resp = client.table("simulations").select("data").eq("user_id", user_id).execute()
    total = 0
    for row in resp.data:
        sim_data = row.get("data", {})
        completed_at_str = sim_data.get("completedAt")
        if completed_at_str and completed_at_str.startswith(reference.isoformat()):
            total += sim_data.get("stats", {}).get("answered", 0)
    return total


def get_flashcards_done_yesterday(reference: date) -> int:
    # A tabela flashcard_progress tem {question_id, data: {lastReviewed}}
    client = _get_client()
    user_id = _get_user_id()
    
    resp = client.table("flashcard_progress").select("data").eq("user_id", user_id).execute()
    total = 0
    ref_iso = reference.isoformat()
    for row in resp.data:
        fc_data = row.get("data", {})
        last_reviewed = fc_data.get("lastReviewed")
        # Se lastReviewed for um ISO string
        if last_reviewed and isinstance(last_reviewed, str) and last_reviewed.startswith(ref_iso):
            total += 1
            
    return total

def get_material_for_topic(macro_topic: str) -> str | None:
    """Busca o material de estudo personalizado do usuário para um determinado macro tema."""
    client = _get_client()
    try:
        resp = client.table("tutor_materials").select("content").eq("macro_topic", macro_topic).limit(1).execute()
        if resp.data and len(resp.data) > 0:
            return resp.data[0]["content"]
    except Exception as e:
        logger.warning(f"Erro ao buscar material para o tópico '{macro_topic}': {e}")
    return None

