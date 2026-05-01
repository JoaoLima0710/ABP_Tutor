import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

from abp_tutor.config import get_settings


def load_cronograma() -> Dict[str, Any]:
    """Carrega o cronograma.json da pasta data."""
    path = Path(__file__).parent.parent.parent / "data" / "cronograma.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_system_prompt() -> str:
    """Carrega o prompt de sistema."""
    path = Path(__file__).parent / "prompts" / "tutor_system.md"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_user_template() -> str:
    """Carrega o template do prompt do usuário."""
    path = Path(__file__).parent / "prompts" / "daily_user_template.md"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_day_for_date(target_date: date) -> Optional[Dict[str, Any]]:
    """Calcula qual dia do cronograma (1-30) corresponde à data alvo."""
    settings = get_settings()
    
    if target_date < settings.START_DATE:
        return None  # Antes do início
        
    days_elapsed = (target_date - settings.START_DATE).days
    day_index = days_elapsed + 1
    
    cronograma = load_cronograma()
    if day_index < 1 or day_index > cronograma["total_days"]:
        return None  # Fora da janela de 30 dias
        
    for day in cronograma["days"]:
        if day["day_index"] == day_index:
            # Add targets to the day dict
            day["questions_target"] = cronograma["default_questions_target"]
            day["flashcards_target"] = cronograma["default_flashcards_target"]
            return day
            
    return None


def render_user_prompt(
    day_plan: Dict[str, Any],
    today: date,
    exam_date: date,
    accuracy: list,
    weak: list,
    compliance_yesterday: Optional[Dict[str, Any]],
    reference_material: Optional[str] = None,
) -> str:
    """Preenche o template com os dados dinâmicos."""
    template = load_user_template()
    
    days_to_exam = (exam_date - today).days
    subtopics_bullets = "\n".join(f"- {s}" for s in day_plan["subtopics"])
    
    acc_json = json.dumps(accuracy, ensure_ascii=False) if accuracy else "[]"
    weak_json = json.dumps(weak, ensure_ascii=False) if weak else "[]"
    
    if compliance_yesterday:
        q_done = compliance_yesterday.get("questions_done", 0)
        q_target = 30 # default
        fc_done = compliance_yesterday.get("flashcards_done", 0)
        fc_target = 20 # default
        t_read = "Sim" if compliance_yesterday.get("text_read") else "Não"
    else:
        q_done = 0
        q_target = 30
        fc_done = 0
        fc_target = 20
        t_read = "Sem dados (primeiro dia ou falha no registro)"

    if reference_material:
        # Limita o tamanho do material de referência por segurança (ex: 30000 caracteres)
        safe_material = reference_material[:30000]
        reference_material_section = f"""# Material Base do Aluno
Utilize o material de referência abaixo como a base ARGUMENTATIVA e de CONTEÚDO PRINCIPAL para a sua revisão. Os diferenciais críticos e armadilhas de prova devem ser extraídos prioritariamente daqui.

{safe_material}"""
    else:
        reference_material_section = ""

    return template.format(
        day_index=day_plan["day_index"],
        plan_date=today.strftime("%d/%m/%Y"),
        days_to_exam=days_to_exam,
        macro_topic=day_plan["macro_topic"],
        subtopics_bullets=subtopics_bullets,
        reference_material_section=reference_material_section,
        accuracy_by_topic_json=acc_json,
        weak_areas_json=weak_json,
        questions_done_yesterday=q_done,
        questions_target_yesterday=q_target,
        flashcards_done_yesterday=fc_done,
        flashcards_target_yesterday=fc_target,
        text_read_yesterday=t_read,
    )

