Hoje é o dia {day_index} de 30 da preparação. Data: {plan_date}. Faltam {days_to_exam} dias para a prova.

# Macro-tema do dia
{macro_topic}

# Subtópicos
{subtopics_bullets}

{reference_material_section}

{review_section}

# Dados de desempenho (últimos 7 dias)
- Acertos por tópico: {accuracy_by_topic_json}
- Top 3 áreas de fraqueza: {weak_areas_json}

# Aderência ontem
- Questões feitas: {questions_done_yesterday} (meta era {questions_target_yesterday})
- Flashcards revisados: {flashcards_done_yesterday} (meta era {flashcards_target_yesterday})
- Texto lido: {text_read_yesterday}

# Sua tarefa
Gere o material do dia. Responda **somente** com um objeto JSON válido (sem markdown fence, sem comentários) com este schema:

{{
  "text_md": "string em Markdown — texto de revisão completo seguindo a estrutura padrão do system prompt",
  "flashcards": [{{"q": "string", "a": "string"}}, ...],
  "priority_areas": ["string", "string"],
  "nudge": "string — 2 linhas, sem clichê, calibrado pela aderência de ontem"
}}

Restrições:
- text_md entre 800 e 1500 palavras
- flashcards: entre 5 e 15 itens (priorize qualidade sobre quantidade)
- priority_areas: exatamente 2 áreas, escolhidas considerando as fraquezas reportadas
- nudge: se aderência ontem foi alta, reconheça brevemente e suba a régua. Se foi baixa, seja firme sem moralismo. Se foi dia 1, dê tom de partida.
