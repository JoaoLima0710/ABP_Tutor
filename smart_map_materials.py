"""
Mapeamento manual definitivo: arquivo → tema do cronograma.

Usa correspondência baseada em palavras-chave no nome do arquivo
e conteúdo identificado nos PDFs. Cobre 100% dos 30 temas do cronograma.
"""

import os
import sys
import json
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from upload_material import upload_material

# ═══════════════════════════════════════════════════════════════
# MAPEAMENTO: palavras-chave no nome do arquivo → tema do cronograma
# A ordem importa: a primeira regra que der match vence.
# ═══════════════════════════════════════════════════════════════

KEYWORD_MAP = [
    # ── Esquizofrenia (dias 1-3) ──
    (["Aula 3 Esquizofrenia", "A3 Esquizofrenia"], "Esquizofrenia e outros transtornos psicóticos — fundamentos"),
    (["Simulado M3 Aula 3"], "Esquizofrenia e outros transtornos psicóticos — fundamentos"),
    (["Gabarito M3 Aula 3"], "Esquizofrenia e outros transtornos psicóticos — fundamentos"),

    # ── Bipolar (dia 6) ──
    (["A4 - Bipolar", "A4 Bipolar", "Bipolar"], "Transtorno bipolar"),
    (["Simulado M3 Aula 4"], "Transtorno bipolar"),
    (["Gabarito M3 Aula 4"], "Transtorno bipolar"),

    # ── Depressão (dias 4-5) ──
    (["A5 Depressão", "A5 Depress", "Depressão Maior", "Depress"], "Transtornos de humor — TDM"),
    (["Simulado M3 Aula 5"], "Transtornos de humor — TDM"),
    (["Gabarito M3 Aula 5"], "Transtornos de humor — TDM"),

    # ── Suicídio (dia 7) ──
    (["A6 Suicídio", "A6 Suic", "Suicídio", "Suicidio"], "Risco de suicídio e crises afetivas"),
    (["Simulado M3 Aula 6"], "Risco de suicídio e crises afetivas"),
    (["Gabarito M3 Aula 6"], "Risco de suicídio e crises afetivas"),

    # ── Ansiedade (dia 8) ──
    (["A7 Ansiedade", "Ansiedade"], "Ansiedade — TAG, pânico, fobias"),
    (["Simulado M3 Aula 7"], "Ansiedade — TAG, pânico, fobias"),
    (["Gabarito M3 Aula 7"], "Ansiedade — TAG, pânico, fobias"),

    # ── TOC (dia 9) ──
    (["A8 TOC", "TOC"], "TOC e espectro obsessivo-compulsivo"),
    (["Simulado M3 Aula 8"], "TOC e espectro obsessivo-compulsivo"),
    (["Gabarito M3 Aula 8"], "TOC e espectro obsessivo-compulsivo"),

    # ── TEPT / Estresse (dia 10) ──
    (["A9 Estresse", "Estresse"], "TEPT e trauma"),
    (["Simulado M3 Aula 9"], "TEPT e trauma"),
    (["Gabarito M3 Aula 9"], "TEPT e trauma"),

    # ── Transtornos alimentares (dia 26) ──
    (["A10 Transtornos Alimentares", "Alimentares"], "Transtornos alimentares e do sono"),
    (["Simulado M3 Aula 10"], "Transtornos alimentares e do sono"),
    (["Gabarito M3 Aula 10"], "Transtornos alimentares e do sono"),

    # ── Somáticos / Interconsulta (dia 22 - catatonia e quadros orgânicos) ──
    (["A11 Somáticos", "A11 Som", "Somáticos", "Somaticos"], "Catatonia e quadros orgânicos"),
    (["Simulado M3 Aula 11"], "Catatonia e quadros orgânicos"),
    (["Gabarito M3 Aula 11"], "Catatonia e quadros orgânicos"),
    (["A12 Interconsulta", "Interconsulta"], "Catatonia e quadros orgânicos"),
    (["Simulado M3 Aula 12"], "Catatonia e quadros orgânicos"),
    (["Gabarito M3 Aula 12"], "Catatonia e quadros orgânicos"),

    # ── Drogas / TUS (dias 11-12) ──
    (["A13 Drogas", "Drogas"], "TUS — outras substâncias"),
    (["Simulado M3 Aula 13"], "TUS — outras substâncias"),
    (["Gabarito M3 Aula 13"], "TUS — outras substâncias"),

    # ── Sono (dia 26 - junto com alimentares) ──
    (["A14 Sono", "Sono"], "Transtornos alimentares e do sono"),
    (["Simulado M3 Aula 14"], "Transtornos alimentares e do sono"),
    (["Gabarito M3 Aula 14"], "Transtornos alimentares e do sono"),

    # ── Impulsividade (dia 25 - personalidade) ──
    (["A15 Impulsividade", "Impulsividade"], "Transtornos de personalidade"),
    (["Simulado M3 Aula 15"], "Transtornos de personalidade"),
    (["Gabarito M3 Aula 15"], "Transtornos de personalidade"),

    # ── Neurocognitivo (dia 17) ──
    (["A16 Neurocognitivo", "Neurocognitivo"], "Transtornos neurocognitivos — demências"),
    (["Simulado M3 Aula 16"], "Transtornos neurocognitivos — demências"),
    (["Gabarito M3 Aula 16"], "Transtornos neurocognitivos — demências"),

    # ── Delirium / Geriátrica (dia 18) ──
    (["Aula 17 Delirium", "Delirium"], "Psiquiatria geriátrica"),
    (["Simulado M3 Aula 17"], "Psiquiatria geriátrica"),
    (["Gabarito M3 Aula 17"], "Psiquiatria geriátrica"),

    # ── Personalidade (dia 25) ──
    (["A2 personalidade", "personalidade"], "Transtornos de personalidade"),
    (["Simulado M3 Aula 2"], "Transtornos de personalidade"),
    (["Gabarito M3 Aula 2"], "Transtornos de personalidade"),

    # ── Desenvolvimento / Infância (dias 14-15) ──
    (["A1 Desenvolvimento", "Desenvolvimento"], "Psiquiatria da infância — neurodesenvolvimento"),
    (["A3 Desenvolvimento"], "Psiquiatria da infância — neurodesenvolvimento"),
    (["Simulado M3 Aula 1"], "Psiquiatria da infância — neurodesenvolvimento"),
    (["Gabarito M3 Aula 1"], "Psiquiatria da infância — neurodesenvolvimento"),

    # ── Farmacologia (dias 19-20) ──
    (["Farmacologia 1"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Farmacologia 2"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Farmacologia 3"], "Psicofarmacologia avançada — efeitos adversos graves"),
    (["Modulo 4 Aula 1"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Simulado M4 Aula 1"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Gabarito M4 Aula 1"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Modulo 4 Aula 2"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Simulado M4 Aula 2"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Gabarito M4 Aula 2"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Modulo 4 Aula 3"], "Psicofarmacologia avançada — efeitos adversos graves"),
    (["Simulado M4 Aula 3"], "Psicofarmacologia avançada — efeitos adversos graves"),
    (["Gabarito M4 Aula 3"], "Psicofarmacologia avançada — efeitos adversos graves"),
    (["Modulo 4 Aula 4"], "Emergências psiquiátricas"),
    (["Simulado M4 Aula 4"], "Emergências psiquiátricas"),
    (["Gabarito M4 Aula 4"], "Emergências psiquiátricas"),

    # ── Saúde Pública / RAPS (dia 13) ──
    (["Modulo 5 Aula 1"], "RAPS, CAPS AD e política brasileira de drogas"),
    (["Simulado M5 Aula 1"], "RAPS, CAPS AD e política brasileira de drogas"),
    (["Gabarito M5 Aula 1"], "RAPS, CAPS AD e política brasileira de drogas"),
    (["Modulo 5 Aula 2"], "RAPS, CAPS AD e política brasileira de drogas"),
    (["Simulado M5 Aula 2"], "RAPS, CAPS AD e política brasileira de drogas"),
    (["Gabarito M5 Aula 2"], "RAPS, CAPS AD e política brasileira de drogas"),

    # ── Leis / Forense / Bioética (dias 23-24) ──
    (["Leis em psiquiatria", "Leis", "Live 6 - Leis"], "Psiquiatria forense"),
    (["cap46forense"], "Psiquiatria forense"),
    (["Ética", "Etica", "História Ética", "R-E"], "Bioética, sigilo e CFM"),

    # ── Psicopatologia → Esquizofrenia fundamentos (dia 1) ──
    (["Psicopatologia"], "Esquizofrenia e outros transtornos psicóticos — fundamentos"),

    # ── Neurociências / Módulos 1-2 genéricos ──
    (["Neurotransmissores"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Neurônios e Receptores", "Neurônios", "Neur"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Neuroimagem", "A4 Neuroimagem"], "Transtornos neurocognitivos — demências"),
    (["Topografia"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Genética", "Gen", "RDoC"], "Psicofarmacologia avançada — interações e CYP450"),

    # ── Tratado ABP (todos os temas - revisão integradora) ──
    (["ABP Tratado", "Tratado"], "Revisão integradora — armadilhas de prova"),
    (["temasdasprovasabp"], "Revisão integradora — armadilhas de prova"),

    # ── Reta Final / Simulados genéricos → Revisão integradora ──
    (["Reta Final"], "Revisão integradora — armadilhas de prova"),
    (["Gabarito Reta Final"], "Revisão integradora — armadilhas de prova"),

    # ── Simulados M1 (questões gerais) ──
    (["Simulado M1"], "Revisão integradora — armadilhas de prova"),
    (["Gabarito M1"], "Revisão integradora — armadilhas de prova"),

    # ── Módulos genéricos sem nome → melhor tema possível ──
    (["Modulo 1 - Aula 1"], "Psiquiatria da infância — neurodesenvolvimento"),
    (["Modulo 1 - Aula 2", "Estudos e Estigma"], "Bioética, sigilo e CFM"),
    (["Modulo 1 - Aula 3"], "Psiquiatria da infância — neurodesenvolvimento"),
    (["Modulo 1 - Aula 4"], "Transtornos neurocognitivos — demências"),
    (["Modulo 2 - Aula 1"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Modulo 2 - Aula 2"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Modulo 2 - Aula 3"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Modulo 2 - Aula 4"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Modulo 3 - Aula 1"], "Psiquiatria da infância — neurodesenvolvimento"),
    (["Modulo 3 - Aula 2"], "Transtornos de personalidade"),
    (["Modulo 3 - Aula 3(1)"], "Esquizofrenia e outros transtornos psicóticos — fundamentos"),
    (["Modulo 3 - Aula 3."], "Esquizofrenia e outros transtornos psicóticos — fundamentos"),
    (["Modulo 3 - Aula 4"], "Transtorno bipolar"),
    (["Modulo 3 - Aula 5"], "Transtornos de humor — TDM"),
    (["Modulo 3 - Aula 6"], "Risco de suicídio e crises afetivas"),
    (["Modulo 3 - Aula 7"], "Ansiedade — TAG, pânico, fobias"),
    (["Modulo 3 - Aula 8"], "TOC e espectro obsessivo-compulsivo"),
    (["Modulo 3 - Aula 10"], "Transtornos alimentares e do sono"),
    (["Modulo 3 - Aula 11"], "Catatonia e quadros orgânicos"),
    (["Modulo 3 - Aula 12"], "Catatonia e quadros orgânicos"),
    (["Modulo 3 - Aula 13"], "TUS — outras substâncias"),
    (["Modulo 3 - Aula 14"], "Transtornos alimentares e do sono"),
    (["Modulo 3 - Aula 15"], "Transtornos de personalidade"),
    (["Modulo 3 - Aula 16"], "Transtornos neurocognitivos — demências"),
    (["Modulo 3 - Aula 17"], "Psiquiatria geriátrica"),

    # ── Simulados M2 (neurociências) ──
    (["Simulado M2 Aula 1"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Simulado M2 Aula 2"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Simulado M2 Aula 3"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Simulado M2 Aula 4"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Gabarito M2 Aula 1", "Gabarito M2 aula 1"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Gabarito M2 aula 2", "Gabarito M2 Aula 2"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Gabarito M2 Aula 3"], "Psicofarmacologia avançada — interações e CYP450"),
    (["Gabarito M2 Aula 4"], "Psicofarmacologia avançada — interações e CYP450"),
]

# ═══════════════════════════════════════════════════════════════
# TEMAS SEM ARQUIVOS DEDICADOS: herdam materiais de temas próximos.
# Após o mapeamento primário, estes são enviados como material compartilhado.
# ═══════════════════════════════════════════════════════════════

SECONDARY_TOPICS = {
    # Tema sem material → lista de (palavras-chave do arquivo fonte, tema fonte)
    "Esquizofrenia — tratamento agudo e manutenção": [
        "Aula 3 Esquizofrenia",   # mesmo conteúdo cobre fundamento + tratamento
        "Simulado M3 Aula 3",
        "Farmacologia 1",
        "Farmacologia 2",
    ],
    "Outros psicóticos": [
        "Aula 3 Esquizofrenia",   # esquizoafetivo, delirante estão no mesmo material
        "Psicopatologia",
    ],
    "TDM — tratamento": [
        "A5 Depressão",           # a aula de depressão cobre tratamento
        "Simulado M3 Aula 5",
        "Farmacologia 2",         # ISRS, IRSN etc
    ],
    "Transtornos por uso de substâncias — álcool": [
        "A13 Drogas",             # drogas genérico cobre álcool
        "Simulado M3 Aula 13",
    ],
    "Psiquiatria da infância — humor e ansiedade": [
        "A1 Desenvolvimento",
        "A7 Ansiedade",           # ansiedade geral serve como base
        "A5 Depressão",           # depressão na infância
    ],
    "Adolescência e transição": [
        "A1 Desenvolvimento",
        "A13 Drogas",             # uso de substâncias na adolescência
        "A6 Suic",                # autolesão
    ],
    "Sexualidade e disforia de gênero": [
        "Psicopatologia",         # base psicopatológica
    ],
    "Psicoterapias — bases": [
        "Psicopatologia",         # bases teóricas
        "A7 Ansiedade",           # TCC
    ],
    "Simulado mental + véspera": [
        "temasdasprovasabp",
        "Reta Final",
    ],
}


def match_file(filename: str) -> str | None:
    """Retorna o tema do cronograma para o arquivo, ou None se não encontrar."""
    stem = Path(filename).stem
    # Normaliza travessão (–) para hífen (-) para matching
    stem_normalized = stem.replace('\u2013', '-').replace('\u2014', '-')
    for keywords, topic in KEYWORD_MAP:
        for kw in keywords:
            if kw.lower() in stem_normalized.lower():
                return topic
    return None


def _match_secondary(filename: str, keywords: list[str]) -> bool:
    """Verifica se o arquivo contém alguma das keywords secundárias."""
    stem = Path(filename).stem
    stem_normalized = stem.replace('\u2013', '-').replace('\u2014', '-').lower()
    return any(kw.lower() in stem_normalized for kw in keywords)


def run_smart_mapping(folder_path: str):
    """Processa todos os arquivos com mapeamento inteligente."""
    if not os.path.isdir(folder_path):
        print(f"Erro: pasta nao encontrada: {folder_path}")
        return

    files = sorted([
        f for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
        and Path(f).suffix.lower() in [".pdf", ".pptx", ".txt", ".md"]
    ])

    # Carrega lista de temas do cronograma
    cron_path = Path(__file__).parent / "data" / "cronograma.json"
    with open(cron_path, "r", encoding="utf-8") as f:
        cronograma = json.load(f)
    all_topics = set(day["macro_topic"] for day in cronograma["days"])

    print(f"\n{'='*60}")
    print(f"MAPEAMENTO INTELIGENTE DE MATERIAIS")
    print(f"Pasta: {folder_path}")
    print(f"Arquivos encontrados: {len(files)}")
    print(f"{'='*60}\n")

    matched = 0
    unmatched = []
    topic_files = {}  # tema -> lista de arquivos

    for fname in files:
        topic = match_file(fname)
        if topic:
            if topic not in topic_files:
                topic_files[topic] = []
            topic_files[topic].append(fname)
            print(f"  ✅ {fname}")
            print(f"     → {topic}")
            full_path = os.path.join(folder_path, fname)
            upload_material(topic, full_path)
            matched += 1
        else:
            unmatched.append(fname)
            print(f"  ❌ {fname} — SEM MATCH")

    # Relatório primário
    covered_topics = set(topic_files.keys())
    missing_topics = all_topics - covered_topics

    # ── SEGUNDA PASSAGEM: Temas secundários ──
    if missing_topics:
        print(f"\n{'='*60}")
        print(f"SEGUNDA PASSAGEM — Mapeamento secundário")
        print(f"{'='*60}\n")

        for sec_topic, sec_keywords in SECONDARY_TOPICS.items():
            if sec_topic not in missing_topics:
                continue  # já coberto
            for fname in files:
                if _match_secondary(fname, sec_keywords):
                    if sec_topic not in topic_files:
                        topic_files[sec_topic] = []
                    if fname not in topic_files[sec_topic]:
                        topic_files[sec_topic].append(fname)
                        print(f"  🔄 {fname}")
                        print(f"     → {sec_topic} (secundário)")
                        full_path = os.path.join(folder_path, fname)
                        upload_material(sec_topic, full_path)
                        matched += 1

    # Relatório final
    covered_topics = set(topic_files.keys())
    missing_topics = all_topics - covered_topics

    print(f"\n{'='*60}")
    print(f"RELATÓRIO FINAL")
    print(f"{'='*60}")
    print(f"Arquivos mapeados: {matched}")
    print(f"Temas cobertos: {len(covered_topics)}/{len(all_topics)}")

    if missing_topics:
        print(f"\n⚠️  Temas SEM material:")
        for t in sorted(missing_topics):
            print(f"   - {t}")

    if unmatched:
        print(f"\n⚠️  Arquivos sem match:")
        for f in unmatched:
            print(f"   - {f}")

    print(f"\n📊 Distribuição por tema:")
    for topic in sorted(topic_files.keys()):
        count = len(topic_files[topic])
        print(f"   {topic}: {count} arquivo(s)")

    print(f"{'='*60}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Mapeamento inteligente de materiais ABP")
    parser.add_argument("folder", help="Caminho para a pasta com os materiais")
    args = parser.parse_args()
    run_smart_mapping(args.folder)
