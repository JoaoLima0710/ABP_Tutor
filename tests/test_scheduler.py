import pytest
from datetime import date
from abp_tutor import scheduler

# Mockando settings no próprio módulo scheduler para os testes
@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    class MockSettings:
        START_DATE = date(2026, 5, 1)
        EXAM_DATE = date(2026, 5, 30)
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
    
    # Dia 30 (30 de maio)
    day = scheduler.get_day_for_date(date(2026, 5, 30))
    assert day is not None
    assert day["day_index"] == 30

def test_get_day_for_date_after_end():
    # Após o fim (31 de maio)
    day = scheduler.get_day_for_date(date(2026, 5, 31))
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
        exam_date=date(2026, 5, 30),
        accuracy=[{"topic": "Ansiedade", "attempted": 10, "correct": 5, "accuracy_pct": 50}],
        weak=[{"topic": "Ansiedade", "subtopic": None, "accuracy_pct": 50, "n_attempts": 10}],
        compliance_yesterday=None
    )
    
    assert "Hoje é o dia 10 de 30" in prompt
    assert "Ansiedade" in prompt
    assert "TAG" in prompt
    assert "Pânico" in prompt
