"""
Logging estruturado (JSON) para o orquestrador.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Formata cada registro como uma linha JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        # Campos extras injetados via `logger.info("msg", extra={...})`
        for key in ("run_id", "plan_date", "status", "day_index"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configura e retorna o logger raiz do pacote."""
    _logger = logging.getLogger("abp_tutor")
    if _logger.handlers:
        return _logger  # já configurado

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    _logger.addHandler(handler)
    _logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    _logger.propagate = False
    return _logger


def _get_logger() -> logging.Logger:
    """Retorna o logger, configurando com o nível do settings se disponível."""
    _logger = logging.getLogger("abp_tutor")
    if not _logger.handlers:
        try:
            from abp_tutor.config import get_settings
            level = get_settings().LOG_LEVEL
        except Exception:
            level = "INFO"
        setup_logging(level)
    return _logger


# Acesso direto — setup lazy no primeiro uso
logger = _get_logger()
