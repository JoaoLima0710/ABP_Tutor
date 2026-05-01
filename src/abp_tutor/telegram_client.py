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


def _md_to_html(text: str) -> str:
    """Converte Markdown simplificado para HTML do Telegram."""
    # Bold: **text** → <b>text</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic: *text* or _text_ → <i>text</i>
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'_(.+?)_', r'<i>\1</i>', text)
    # Code: `text` → <code>text</code>
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # Headers: ## text → <b>text</b> com newline
    text = re.sub(r'^#{1,4}\s+(.+)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    # Escape HTML special chars that aren't part of our tags
    # (must be done carefully to not break our own tags)
    return text


def _escape_html(text: str) -> str:
    """Escapa caracteres HTML, preservando tags que nós mesmos inserimos."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def _split_message(text: str) -> List[str]:
    """Splits a long text into chunks respecting Telegram's limit."""
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
            if len(paragraph) > MAX_TELEGRAM_MESSAGE_LENGTH:
                lines = paragraph.split('\n')
                for line in lines:
                    if len(current_chunk) + len(line) + 1 <= MAX_TELEGRAM_MESSAGE_LENGTH:
                        if current_chunk:
                            current_chunk += "\n"
                        current_chunk += line
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = line
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph
                
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks


def _send_text(text: str, parse_mode: str = "HTML") -> None:
    settings = get_settings()
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("Falha ao enviar Telegram", extra={
                "status": e.response.status_code,
                "text": e.response.text[:500]
            })
            # Fallback: tenta sem parse_mode se HTML falhou
            if parse_mode == "HTML":
                logger.info("Tentando envio sem formatacao...")
                payload["parse_mode"] = ""
                resp2 = client.post(url, json=payload)
                resp2.raise_for_status()
            else:
                raise


def _send_pdf(pdf_path: str, filename: str) -> None:
    settings = get_settings()
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendDocument"
    
    data = {"chat_id": settings.TELEGRAM_CHAT_ID}
    with open(pdf_path, "rb") as f:
        files = {"document": (filename, f, "application/pdf")}
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, data=data, files=files)
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error("Falha ao enviar PDF via Telegram", extra={
                    "status": e.response.status_code,
                    "text": e.response.text[:500]
                })
                raise


def send_alert(message: str) -> None:
    """Envia uma mensagem de alerta simples (sem formatacao)."""
    try:
        _send_text(message, parse_mode="")
    except Exception as e:
        logger.error(f"Falha ao enviar alerta Telegram: {e}")


def send_daily_package(plan_date: date, day_plan: Dict[str, Any], tutor_result: Dict[str, Any]) -> None:
    """Envia o pacote completo formatado e segmentado para o Telegram."""
    settings = get_settings()
    days_to_exam = (settings.EXAM_DATE - plan_date).days
    
    subtopics = ", ".join(day_plan["subtopics"])
    nudge_text = _escape_html(tutor_result.get("nudge", ""))
    macro_topic = _escape_html(day_plan["macro_topic"])
    subtopics_escaped = _escape_html(subtopics)
    
    # 1. Cabecalho
    header = (
        f"📚 <b>Dia {day_plan['day_index']}/30 — Tutor ABP</b>\n"
        f"🗓 {plan_date.strftime('%d/%m/%Y')} · Faltam <b>{days_to_exam}</b> dias\n\n"
        f"🎯 <b>Tema do dia:</b> {macro_topic}\n"
        f"📌 <b>Subtopicos:</b> {subtopics_escaped}\n\n"
        f"<b>Metas de hoje:</b>\n"
        f"• Questoes: {day_plan['questions_target']}\n"
        f"• Flashcards: {day_plan['flashcards_target']}\n"
        f"• Texto de revisao (abaixo)\n\n"
        f"💬 <i>{nudge_text}</i>"
    )
    _send_text(header)
    
    # 2. Texto de Revisao (convertido de MD para HTML)
    text_html = _md_to_html(tutor_result["text_md"])
    chunks = _split_message(text_html)
    for chunk in chunks:
        _send_text(chunk)
        
    # 3. Priority Areas
    p_items = "\n".join([f"• {_escape_html(a)}" for a in tutor_result["priority_areas"]])
    p_text = f"🚨 <b>Foco nas Questoes de Hoje</b>\nSua prioridade no banco de questoes deve ser:\n{p_items}"
    _send_text(p_text)
    
    # 4. Flashcards
    fc_text = "💡 <b>Flashcards do Dia</b>\n\n"
    for i, fc in enumerate(tutor_result["flashcards"]):
        q = _escape_html(fc["q"])
        a = _escape_html(fc["a"])
        fc_text += f"❓ <b>{i+1}. {q}</b>\n👉 <i>{a}</i>\n\n"
        
    fc_chunks = _split_message(fc_text.strip())
    for chunk in fc_chunks:
        _send_text(chunk)

    # 5. Gerar PDF para impressao
    try:
        pdf_md = f"# Dia {day_plan['day_index']}/30 — Tutor ABP\n\n"
        pdf_md += f"**Data:** {plan_date.strftime('%d/%m/%Y')}\n\n"
        pdf_md += f"**Tema:** {day_plan['macro_topic']}\n\n"
        pdf_md += f"**Subtopicos:** {subtopics}\n\n"
        pdf_md += "---\n\n"
        pdf_md += f"{tutor_result['text_md']}\n\n"
        pdf_md += "---\n\n"
        pdf_md += "## Prioridade nas Questoes\n\n"
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
        logger.error(f"Erro ao gerar/enviar PDF para impressao: {e}")
