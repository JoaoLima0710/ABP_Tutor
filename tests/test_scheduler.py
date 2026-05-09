import pytest
from datetime import date
from abp_tutor import scheduler

# Mockando settings no próprio módulo scheduler para os testes
@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    class MockSettings:
        START_DATE = date(2026, 5, 1)
        EXAM_DATE = date(2026, 6, 7)
    monkeypatch.setattr(scheduler, "get_settings", lambda: MockSettings())

def test_get_day_for_date_before_start():
    # Antes do início (30 de abril)
    day = scheduler.get_day_for_date(date(2026, 4, 30))
    assert day is None

def test_get_day_for_date_valid():
    # Dia 1 (1 de maio)
    day = scheduler.get_day_for_date(date(2026, 5, 1))
    assert day is not None
    assert day["day_index"] == 1
    assert "Esquizofrenia" in day["macro_topic"]

    # Dia 37 (06/06 — véspera)
    day = scheduler.get_day_for_date(date(2026, 6, 6))
    assert day is not None
    assert day["day_index"] == 37

def test_get_day_for_date_after_end():
    # Após o fim — dia da prova (07/06) está fora da janela de revisão
    day = scheduler.get_day_for_date(date(2026, 6, 7))
    assert day is None

def test_render_user_prompt():
    day_plan = {
        "day_index": 10,
        "macro_topic": "Ansiedade",
        "subtopics": ["TAG", "Pânico"],
        "questions_target": 30,
        "flashcards_target": 20
    }

    prompt = scheduler.render_user_prompt(
        day_plan=day_plan,
        today=date(2026, 5, 10),
        exam_date=date(2026, 6, 7),
        accuracy=[{"topic": "Ansiedade", "attempted": 10, "correct": 5, "accuracy_pct": 50}],
        weak=[{"topic": "Ansiedade", "subtopic": None, "accuracy_pct": 50, "n_attempts": 10}],
        compliance_yesterday=None
    )

    assert "Ansiedade" in prompt
    assert "TAG" in prompt
    assert "Pânico" in prompt
    # Códigos M*A* são internos (locator de arquivos do Claude Code) — nunca devem
    # ser injetados explicitamente como seção do prompt do tutor remoto.
    assert "Aulas de referência" not in prompt
    assert "aulas_codigos" not in prompt
