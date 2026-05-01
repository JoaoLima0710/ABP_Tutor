import os
import sys
import json
import argparse
from pathlib import Path
from difflib import get_close_matches

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from upload_material import upload_material

def load_topics():
    path = Path(__file__).parent / "data" / "cronograma.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [day["macro_topic"] for day in data["days"]]

def batch_process(folder_path: str):
    if not os.path.isdir(folder_path):
        print(f"Erro: O caminho especificado não é uma pasta: {folder_path}")
        return

    topics = load_topics()
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    print(f"Iniciando processamento em lote da pasta: {folder_path}")
    print(f"Encontrados {len(files)} arquivos. Tentando associar aos temas do cronograma...")
    
    matches_found = 0
    for filename in files:
        # Tenta encontrar o melhor match do nome do arquivo com a lista de tópicos
        # Remove a extensão para comparar
        name_without_ext = Path(filename).stem
        
        # Busca por match aproximado (cutoff alto para evitar erros)
        best_matches = get_close_matches(name_without_ext, topics, n=1, cutoff=0.3)
        
        if best_matches:
            topic = best_matches[0]
            print(f"\n- Arquivo: '{filename}' -> Topico associado: '{topic}'")
            full_path = os.path.join(folder_path, filename)
            upload_material(topic, full_path)
            matches_found += 1
        else:
            # Tenta busca por substring simples caso o fuzzy falhe
            found_substring = False
            for topic in topics:
                if topic.lower() in name_without_ext.lower() or name_without_ext.lower() in topic.lower():
                    print(f"\n- Arquivo: '{filename}' -> Topico associado (via busca): '{topic}'")
                    full_path = os.path.join(folder_path, filename)
                    upload_material(topic, full_path)
                    matches_found += 1
                    found_substring = True
                    break
            
            if not found_substring:
                print(f"\n[!] Arquivo: '{filename}' -> Nenhum topico correspondente encontrado.")

    print(f"\n" + "="*50)
    print(f"Processamento concluido!")
    print(f"Total de arquivos processados com sucesso: {matches_found}")
    print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Processamento em lote de materiais ABP")
    parser.add_argument("folder", help="Caminho para a pasta contendo os arquivos (PDF, PPTX, etc)")
    
    args = parser.parse_args()
    batch_process(args.folder)
