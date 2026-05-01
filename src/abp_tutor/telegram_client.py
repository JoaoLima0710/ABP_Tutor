import re
import os
import tempfile
from datetime import date
from typing import Dict, Any, List

import httpx
from markdown_pdf import MarkdownPdf, Section

from abp_tutor.config import get_settings
from abp_tutor.logging_setup import logger

MAX_TELEGRAM_MESSAGE_LENGTH = 4096

def escape_markdown_v2(text: str) -> str:
    """Escapes characters for Telegram MarkdownV2."""
    # Characters that need escaping in MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    # Remove existing escapes to avoid double escaping, then escape all
    text = re.sub(r'\\([_*\[\]()~`>#+\-=|{}.!])', r'\1', text)
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def _split_message(text: str) -> List[str]:
    """Splits a long markdown text into chunks respecting Telegram's limit."""
    if len(text) <= MAX_TELEGRAM_MESSAGE_LENGTH:
        return [text]
        
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 <= MAX_TELEGRAM_MESSAGE_LENGTH:
            if current_chunk:
                current_chunk += "\n\n"
            current_chunk += paragraph
        else:
            # If a single paragraph is too long (rare but possible), split by newline
            if len(paragraph) > MAX_TELEGRAM_MESSAGE_LENGTH:
                lines = paragraph.split('\n')
                for line in lines:
                    if len(current_chunk) + len(line) + 1 <= MAX_TELEGRAM_MESSAGE_LENGTH:
                        if current_chunk:
                            current_chunk += "\n"
                        current_chunk += line
                    else:
                        chunks.append(current_chunk)
                        current_chunk = line
            else:
                chunks.append(current_chunk)
                current_chunk = paragraph
                
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def _send_text(text: str, parse_mode: str = "MarkdownV2") -> None:
    settings = get_settings()
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    
    with httpx.Client() as client:
        resp = client.post(url, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("Falha ao enviar Telegram", extra={"status": e.response.status_code, "text": e.response.text})
            raise

def _send_pdf(pdf_path: str, filename: str) -> None:
    settings = get_settings()
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendDocument"
    
    data = {"chat_id": settings.TELEGRAM_CHAT_ID}
    with open(pdf_path, "rb") as f:
        files = {"document": (filename, f, "application/pdf")}
        with httpx.Client() as client:
            resp = client.post(url, data=data, files=files)
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error("Falha ao enviar PDF via Telegram", extra={"status": e.response.status_code, "text": e.response.text})
                raise

def send_alert(message: str) -> None:
    """Envia uma mensagem de alerta simples (sem markdown pesado)."""
    try:
        _send_text(message, parse_mode="")
    except Exception as e:
        logger.error(f"Falha ao enviar alerta Telegram: {e}")

def send_daily_package(plan_date: date, day_plan: Dict[str, Any], tutor_result: Dict[str, Any]) -> None:
    """Envia o pacote completo formatado e segmentado para o Telegram."""
    settings = get_settings()
    days_to_exam = (settings.EXAM_DATE - plan_date).days
    
    # 1. Cabeçalho
    subtopics = ", ".join(day_plan["subtopics"])
    header = f"""📚 *Dia {day_plan['day_index']}/30 — Tutor ABP*
🗓 {plan_date.strftime('%d/%m/%Y')} \\· Faltam *{days_to_exam}* dias

🎯 *Tema do dia:* {escape_markdown_v2(day_plan['macro_topic'])}
📌 *Subtópicos:* {escape_markdown_v2(subtopics)}

*Metas de hoje:*
• Questões: {day_plan['questions_target']}
• Flashcards: {day_plan['flashcards_target']}
• Texto de revisão \\(abaixo\\)

💬 _{escape_markdown_v2(tutor_result['nudge'])}_"""

    _send_text(header)
    
    # 2. Texto de Revisão (split)
    # The tutor result text_md is likely already markdown, but Telegram MarkdownV2 is very strict.
    # We apply the escape function, but this might escape intended formatting like **bold**.
    # A cleaner approach for the main body if it uses complex markdown is to parse or just send it raw, 
    # but since the system prompt outputs raw markdown we must convert it carefully or just send as plain text 
    # if it's too complex. For now we use our escape_markdown_v2.
    text_escaped = escape_markdown_v2(tutor_result["text_md"])
    # Re-enable bold
    text_escaped = text_escaped.replace(r'\*\*', '*')
    
    chunks = _split_message(text_escaped)
    for chunk in chunks:
        _send_text(chunk)
        
    # 3. Priority Areas
    p_areas = "\n".join([f"• {escape_markdown_v2(a)}" for a in tutor_result["priority_areas"]])
    p_text = f"🚨 *Foco nas Questões de Hoje*\nSua prioridade no banco de questões deve ser:\n{p_areas}"
    _send_text(p_text)
    
    # 4. Flashcards
    fc_text = "💡 *Flashcards do Dia*\n\n"
    for i, fc in enumerate(tutor_result["flashcards"]):
        q = escape_markdown_v2(fc["q"])
        a = escape_markdown_v2(fc["a"])
        fc_text += f"❓ *{i+1}\\. {q}*\n👉 _{a}_\n\n"
        
    fc_chunks = _split_message(fc_text.strip())
    for chunk in fc_chunks:
        _send_text(chunk)

    # 5. Gerar PDF para impressão
    try:
        pdf_md = f"# Dia {day_plan['day_index']}/30 — Tutor ABP\n\n"
        pdf_md += f"**Data:** {plan_date.strftime('%d/%m/%Y')}\n\n"
        pdf_md += f"**Tema:** {day_plan['macro_topic']}\n\n"
        pdf_md += f"**Subtópicos:** {subtopics}\n\n"
        pdf_md += "---\n\n"
        pdf_md += f"{tutor_result['text_md']}\n\n"
        pdf_md += "---\n\n"
        pdf_md += "## Prioridade nas Questões\n\n"
        for a in tutor_result["priority_areas"]:
            pdf_md += f"- {a}\n"
        pdf_md += "\n---\n\n"
        pdf_md += "## Flashcards\n\n"
        for i, fc in enumerate(tutor_result["flashcards"]):
            pdf_md += f"**{i+1}. {fc['q']}**\n\n_{fc['a']}_\n\n"
            
        pdf = MarkdownPdf(toc_level=0)
        pdf.add_section(Section(pdf_md))
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        
        pdf.save(tmp_path)
        
        _send_pdf(tmp_path, f"Resumo_ABP_Dia_{day_plan['day_index']}.pdf")
        os.unlink(tmp_path)
    except Exception as e:
        logger.error(f"Erro ao gerar/enviar PDF para impressão: {e}")
