-- =====================================================
-- ABP Tutor — Tabela para materiais do usuário (RAG)
-- Execute no Supabase Dashboard → SQL Editor → New query
-- =====================================================

CREATE TABLE IF NOT EXISTS tutor_materials (
    macro_topic TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS — permitir acesso via anon key (single-user)
ALTER TABLE tutor_materials ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all for anon on tutor_materials" ON tutor_materials FOR ALL USING (true) WITH CHECK (true);
