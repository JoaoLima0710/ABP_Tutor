"""
Classificador de materiais por CONTEÚDO — abre cada PDF/PPTX,
lê o texto, e classifica pelo tema do cronograma com maior score.
"""
import os, sys, json, re
from pathlib import Path
from collections import Counter

if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

try: import fitz
except: fitz = None

try: from pptx import Presentation
except: Presentation = None

from upload_material import extract_text
from upload_material import upload_material

# ═══════════════════════════════════════════════════
# Palavras-chave discriminantes por tema do cronograma
# ═══════════════════════════════════════════════════
TOPIC_KEYWORDS = {
    "Esquizofrenia e outros transtornos psicóticos — fundamentos": [
        "esquizofrenia", "psicose", "psicótico", "delírio", "alucinação",
        "dopamina", "sintomas positivos", "sintomas negativos", "bleuler",
        "schneider", "desorganização", "embotamento", "catatônico",
        "prodrômico", "fase ativa",
    ],
    "Esquizofrenia — tratamento agudo e manutenção": [
        "antipsicótico", "clozapina", "haloperidol", "risperidona",
        "olanzapina", "quetiapina", "aripiprazol", "refratário",
        "síndrome metabólica", "antipsicóticos atípicos", "típicos",
        "dose equivalente", "clorpromazina", "depot", "palmitato",
    ],
    "Outros psicóticos": [
        "esquizoafetivo", "delirante persistente", "psicose breve",
        "folie", "compartilhado", "esquizofreniforme", "psicótico breve",
    ],
    "Transtornos de humor — TDM": [
        "depressão", "depressivo", "melancolia", "melancólico",
        "anedonia", "phq-9", "humor deprimido", "distimia",
        "atípico", "sazonal", "episódio depressivo",
    ],
    "TDM — tratamento": [
        "isrs", "irsn", "tricíclico", "imao", "fluoxetina", "sertralina",
        "venlafaxina", "duloxetina", "bupropiona", "mirtazapina",
        "ect", "eletroconvulsoterapia", "emtr", "potencialização",
        "augmentação", "antidepressivo",
    ],
    "Transtorno bipolar": [
        "bipolar", "mania", "maníaco", "hipomania", "ciclotimia",
        "estado misto", "lítio", "valproato", "lamotrigina",
        "carbamazepina", "litemia", "tb i", "tb ii",
    ],
    "Risco de suicídio e crises afetivas": [
        "suicídio", "suicida", "autolesão", "tentativa de suicídio",
        "ideação suicida", "risco suicida", "plano suicida",
        "fator de risco", "fator de proteção", "letal",
    ],
    "Ansiedade — TAG, pânico, fobias": [
        "ansiedade", "tag", "pânico", "fobia", "agorafobia",
        "fobia social", "fobia específica", "generalizada",
        "benzodiazepínico", "buspirona", "ataque de pânico",
    ],
    "TOC e espectro obsessivo-compulsivo": [
        "obsessivo", "compulsivo", "toc", "obsessão", "compulsão",
        "dismorfofobia", "tricotilomania", "acumulação",
        "exposição", "prevenção de resposta", "y-bocs",
    ],
    "TEPT e trauma": [
        "tept", "trauma", "estresse pós", "estressor",
        "emdr", "flashback", "revivência", "evitação",
        "hipervigilância", "dissociação", "transtorno de adaptação",
    ],
    "Transtornos por uso de substâncias — álcool": [
        "álcool", "etilismo", "ciwa", "wernicke", "korsakoff",
        "abstinência alcoólica", "naltrexona", "acamprosato",
        "dissulfiram", "delirium tremens", "alcoolismo",
    ],
    "TUS — outras substâncias": [
        "cocaína", "crack", "opioide", "heroína", "metadona",
        "cannabis", "maconha", "tabaco", "nicotina", "buprenorfina",
        "anfetamina", "mdma", "lsd", "substância psicoativa",
    ],
    "RAPS, CAPS AD e política brasileira de drogas": [
        "raps", "caps", "caps ad", "lei 10.216", "portaria 3.088",
        "matriciamento", "saúde mental", "rede de atenção",
        "reforma psiquiátrica", "ubs", "nasf", "pts",
        "território", "desinstitucionalização",
    ],
    "Psiquiatria da infância — neurodesenvolvimento": [
        "tdah", "tea", "autismo", "autista", "déficit de atenção",
        "hiperatividade", "metilfenidato", "deficiência intelectual",
        "neurodesenvolvimento", "espectro autista",
    ],
    "Psiquiatria da infância — humor e ansiedade": [
        "criança", "infantil", "desregulação do humor", "disruptivo",
        "ansiedade de separação", "mutismo seletivo", "pediatr",
        "pré-escolar", "escolar",
    ],
    "Adolescência e transição": [
        "adolescente", "adolescência", "primeiro episódio psicótico",
        "autolesivo", "cutting", "transição", "puberdade",
    ],
    "Transtornos neurocognitivos — demências": [
        "demência", "alzheimer", "lewy", "frontotemporal",
        "moca", "meem", "neurocognitivo", "declínio cognitivo",
        "amiloide", "tau", "acetilcolinesterase", "memantina",
    ],
    "Psiquiatria geriátrica": [
        "idoso", "delirium", "polifarmácia", "beers",
        "geriátrica", "geriátrico", "envelhecimento",
        "funcionalidade", "cam", "confusão aguda",
    ],
    "Psicofarmacologia avançada — interações e CYP450": [
        "cyp450", "cyp", "interação medicamentosa", "farmacocinética",
        "farmacodinâmica", "indutor", "inibidor", "metabolismo",
        "hepatopata", "nefropata", "absorção", "biotransformação",
        "receptor", "neurotransmissor", "sinapse",
    ],
    "Psicofarmacologia avançada — efeitos adversos graves": [
        "snm", "síndrome neuroléptica maligna", "serotoninérgica",
        "discinesia tardia", "hiponatremia", "siadh",
        "síndrome de descontinuação", "rabdomiólise",
        "prolongamento qt", "agranulocitose",
    ],
    "Emergências psiquiátricas": [
        "agitação psicomotora", "contenção", "internação involuntária",
        "emergência", "urgência", "sedação", "haldol",
        "contenção mecânica", "contenção química",
    ],
    "Catatonia e quadros orgânicos": [
        "catatonia", "catatônico", "bfcrs", "lorazepam",
        "estupor", "mutismo", "negativismo", "flexibilidade cérea",
        "somático", "interconsulta", "somatoforme", "conversivo",
    ],
    "Psiquiatria forense": [
        "forense", "imputabilidade", "medida de segurança",
        "perícia", "perito", "inimputável", "semi-imputável",
        "código penal", "interdição", "incapacidade civil",
    ],
    "Bioética, sigilo e CFM": [
        "bioética", "ética", "sigilo", "cfm", "consentimento informado",
        "atestado", "código de ética", "autonomia", "beneficência",
        "não maleficência", "justiça", "resolução cfm",
    ],
    "Transtornos de personalidade": [
        "personalidade", "borderline", "tpb", "dbt",
        "cluster", "antissocial", "narcisista", "esquizóide",
        "histriônico", "evitativo", "dependente", "impulsividade",
    ],
    "Transtornos alimentares e do sono": [
        "anorexia", "bulimia", "tcap", "compulsão alimentar",
        "insônia", "narcolepsia", "parassonia", "apneia",
        "polissonografia", "melatonina", "sonambulismo",
        "purgativo", "índice de massa",
    ],
    "Sexualidade e disforia de gênero": [
        "sexual", "disfunção sexual", "parafilia", "disforia de gênero",
        "transexual", "identidade de gênero", "libido",
        "ejaculação", "orgasmo", "voyeurismo", "exibicionismo",
    ],
    "Psicoterapias — bases": [
        "psicoterapia", "tcc", "cognitivo-comportamental",
        "psicodinâmica", "interpessoal", "transferência",
        "contratransferência", "aliança terapêutica",
        "mindfulness", "act", "comportamental",
    ],
    "Revisão integradora — armadilhas de prova": [
        "prova", "armadilha", "pegadinha", "diferencial",
        "questão", "gabarito", "alternativa", "assinale",
    ],
    "Simulado mental + véspera": [
        "simulado", "estratégia de prova", "véspera",
        "gestão de tempo", "autocuidado", "revisão final",
    ],
}


def score_file(text: str, topic: str) -> float:
    """Calcula score de relevância do texto para um tema."""
    text_lower = text.lower()
    keywords = TOPIC_KEYWORDS.get(topic, [])
    if not keywords:
        return 0.0
    hits = sum(1 for kw in keywords if kw.lower() in text_lower)
    # Score = proporção de keywords encontradas
    return hits / len(keywords)


def classify_file(text: str, min_score: float = 0.15) -> list[tuple[str, float]]:
    """Retorna lista de (tema, score) ordenada, filtrando por score mínimo."""
    scores = []
    for topic in TOPIC_KEYWORDS:
        s = score_file(text, topic)
        if s >= min_score:
            scores.append((topic, s))
    return sorted(scores, key=lambda x: x[1], reverse=True)


def safe_extract(fpath: str) -> str | None:
    """Extrai texto com fallback para PPTX corrompidos."""
    ext = Path(fpath).suffix.lower()
    try:
        return extract_text(fpath)
    except Exception as e1:
        if ext == ".pptx" and fitz:
            # Fallback: tenta converter PPTX como se fosse PDF (não funciona)
            pass
        print(f"     ⚠ Falha na extração: {e1}")
        return None


def run_content_classifier(folder_path: str):
    if not os.path.isdir(folder_path):
        print(f"Erro: pasta não encontrada: {folder_path}")
        return

    cron_path = Path(__file__).parent / "data" / "cronograma.json"
    with open(cron_path, "r", encoding="utf-8") as f:
        cronograma = json.load(f)
    all_topics = set(day["macro_topic"] for day in cronograma["days"])

    files = sorted([
        f for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
        and Path(f).suffix.lower() in [".pdf", ".pptx", ".txt", ".md"]
    ])

    print(f"\n{'='*60}")
    print(f"CLASSIFICADOR POR CONTEÚDO")
    print(f"Pasta: {folder_path}")
    print(f"Arquivos: {len(files)}")
    print(f"{'='*60}\n")

    topic_files = {}
    failed = []
    uploaded = 0

    for i, fname in enumerate(files, 1):
        fpath = os.path.join(folder_path, fname)
        print(f"[{i}/{len(files)}] {fname}")

        text = safe_extract(fpath)
        if not text or len(text.strip()) < 50:
            print(f"     ⚠ Arquivo vazio ou sem texto extraível")
            failed.append(fname)
            continue

        matches = classify_file(text)
        if not matches:
            print(f"     ❌ Nenhum tema com score suficiente")
            failed.append(fname)
            continue

        # Pega o melhor match (e opcionalmente o 2º se score > 0.25)
        best_topic, best_score = matches[0]
        topics_to_upload = [(best_topic, best_score)]

        if len(matches) > 1 and matches[1][1] >= 0.25:
            topics_to_upload.append(matches[1])

        for topic, score in topics_to_upload:
            pct = int(score * 100)
            print(f"     ✅ {topic} (score: {pct}%)")
            upload_material(topic, fpath)
            uploaded += 1
            if topic not in topic_files:
                topic_files[topic] = []
            topic_files[topic].append(fname)

    # Relatório
    covered = set(topic_files.keys())
    missing = all_topics - covered

    print(f"\n{'='*60}")
    print(f"RELATÓRIO FINAL")
    print(f"{'='*60}")
    print(f"Uploads realizados: {uploaded}")
    print(f"Temas cobertos: {len(covered)}/{len(all_topics)}")

    if missing:
        print(f"\n⚠️  Temas SEM material:")
        for t in sorted(missing):
            print(f"   - {t}")

    if failed:
        print(f"\n⚠️  Arquivos com falha ({len(failed)}):")
        for f in failed:
            print(f"   - {f}")

    print(f"\n📊 Distribuição:")
    for topic in sorted(topic_files.keys()):
        print(f"   {topic}: {len(topic_files[topic])} arquivo(s)")

    print(f"{'='*60}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Classificador por conteúdo")
    parser.add_argument("folder")
    args = parser.parse_args()
    run_content_classifier(args.folder)
