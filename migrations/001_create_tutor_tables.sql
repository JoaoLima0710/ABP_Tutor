-- =====================================================
-- ABP Tutor — Tabelas de estado do orquestrador
-- Execute no Supabase Dashboard → SQL Editor → New query
-- =====================================================

-- 1. Plano gerado para cada dia
CREATE TABLE IF NOT EXISTS tutor_daily_plan (
    id BIGSERIAL PRIMARY KEY,
    plan_date DATE NOT NULL UNIQUE,
    day_index INT NOT NULL,
    macro_topic TEXT NOT NULL,
    subtopics JSONB NOT NULL,
    text_md TEXT NOT NULL,
    flashcards JSONB NOT NULL,             -- [{q, a}, ...]
    priority_areas JSONB NOT NULL,         -- ["...", "..."]
    nudge TEXT,
    questions_target INT NOT NULL DEFAULT 30,
    flashcards_target INT NOT NULL DEFAULT 20,
    text_word_count INT,
    model_used TEXT,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    delivered_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_tutor_plan_date ON tutor_daily_plan(plan_date);

-- 2. Aderência: o que o estudante de fato fez no dia
CREATE TABLE IF NOT EXISTS tutor_daily_compliance (
    plan_date DATE PRIMARY KEY REFERENCES tutor_daily_plan(plan_date),
    questions_done INT DEFAULT 0,
    flashcards_done INT DEFAULT 0,
    text_read BOOLEAN DEFAULT FALSE,
    accuracy_pct NUMERIC(5,2),
    notes TEXT,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Log de execução do orquestrador (para debug)
CREATE TABLE IF NOT EXISTS tutor_run_log (
    id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status TEXT,                            -- 'success' | 'partial' | 'error' | 'skipped'
    error_message TEXT,
    plan_date DATE
);

CREATE INDEX IF NOT EXISTS idx_tutor_run_log_started ON tutor_run_log(started_at DESC);

-- 4. RLS — permitir acesso via anon key (single-user)
ALTER TABLE tutor_daily_plan ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_daily_compliance ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_run_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all for anon" ON tutor_daily_plan FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for anon" ON tutor_daily_compliance FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for anon" ON tutor_run_log FOR ALL USING (true) WITH CHECK (true);
