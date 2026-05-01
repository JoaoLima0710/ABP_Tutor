import json
import time
from typing import Dict, Any

import httpx

from abp_tutor.config import get_settings
from abp_tutor.logging_setup import logger


def generate_daily_content(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """
    Chama a API do POE (OpenAI-compatible) e devolve dict validado
    com text_md, flashcards, priority_areas, nudge.
    """
    settings = get_settings()
    url = "https://api.poe.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.POE_API_KEY}",
        "Content-Type": "application/json",
    }
    
    # Adicionando instruções extras no system prompt para forçar JSON no POE
    json_enforcement = "\n\nCRÍTICO: Responda APENAS com um objeto JSON válido, sem NENHUM texto extra ou marcação Markdown (sem ```json). Comece com { e termine com }."
    augmented_system = system_prompt + json_enforcement
    
    current_user_prompt = user_prompt
    
    with httpx.Client(timeout=300.0) as client:
        for attempt in range(1, 4):
            try:
                payload = {
                    "model": settings.POE_BOT_NAME,
                    "messages": [
                        {"role": "system", "content": augmented_system},
                        {"role": "user", "content": current_user_prompt},
                    ],
                    "temperature": 0.2, # Baixa temperatura para JSON consistente
                    "stream": True,
                }
                
                logger.info("Chamando POE API (em modo stream)", extra={"attempt": attempt, "model": settings.POE_BOT_NAME})
                raw_text = ""
                
                with client.stream("POST", url, headers=headers, json=payload) as resp:
                    resp.raise_for_status()
                    for line in resp.iter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if content:
                                    raw_text += content
                            except Exception:
                                pass
                
                raw_text = raw_text.strip()
                if not raw_text:
                    raise ValueError("Resposta vazia da API")
                    
                # Limpa fences markdown se vierem
                if raw_text.startswith("```"):
                    lines = raw_text.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    raw_text = "\n".join(lines).strip()
                    
                parsed = json.loads(raw_text)
                _validate_payload(parsed)
                
                parsed["model_used"] = settings.POE_BOT_NAME
                return parsed

            except httpx.HTTPStatusError as e:
                logger.warning("POE API HTTP Error", extra={"status": e.response.status_code, "text": e.response.text})
                if attempt == 3 or e.response.status_code not in (429, 500, 502, 503, 504):
                    raise
                time.sleep(2 ** attempt)
                
            except httpx.ReadTimeout as e:
                logger.warning("POE API Timeout", extra={"attempt": attempt})
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)

            except (json.JSONDecodeError, ValueError) as e:
                logger.warning("Erro de validação/JSON do POE", extra={"error": str(e), "raw": raw_text[:200]})
                if attempt == 3:
                    raise
                current_user_prompt += f"\n\n# CORREÇÃO\nA resposta anterior foi inválida ({str(e)}). Retorne APENAS o JSON válido, sem mais nada."


def _validate_payload(data: dict) -> None:
    required = {"text_md", "flashcards", "priority_areas", "nudge"}
    if not required.issubset(data.keys()):
        raise ValueError(f"Faltam chaves: {required - data.keys()}")
    
    if not isinstance(data["flashcards"], list):
         raise ValueError("flashcards não é uma lista")
         
    if not (5 <= len(data["flashcards"]) <= 15):
        raise ValueError(f"flashcards fora da faixa 5-15 (veio {len(data['flashcards'])})")
        
    if not isinstance(data["priority_areas"], list) or len(data["priority_areas"]) != 2:
        raise ValueError("priority_areas precisa ter exatamente 2 itens")
        
    word_count = len(data["text_md"].split())
    if word_count < 300:
        raise ValueError(f"text_md muito curto ({word_count} palavras)")
