-- =====================================================
-- ABP Tutor — Corrige tutor_materials para aceitar
-- múltiplos materiais por tópico
-- Execute no Supabase Dashboard → SQL Editor → New query
-- =====================================================

-- 1. Dropar a tabela antiga (PK era macro_topic, só 1 registro por tema)
DROP TABLE IF EXISTS tutor_materials;

-- 2. Recriar com suporte a múltiplos materiais por tópico
CREATE TABLE tutor_materials (
    id BIGSERIAL PRIMARY KEY,
    macro_topic TEXT NOT NULL,
    source_file TEXT NOT NULL,               -- nome do arquivo de origem
    content TEXT NOT NULL,
    char_count INT GENERATED ALWAYS AS (length(content)) STORED,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(macro_topic, source_file)         -- evita duplicatas do mesmo arquivo
);

CREATE INDEX idx_tutor_materials_topic ON tutor_materials(macro_topic);

-- 3. RLS
ALTER TABLE tutor_materials ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all for anon on tutor_materials"
    ON tutor_materials FOR ALL USING (true) WITH CHECK (true);
