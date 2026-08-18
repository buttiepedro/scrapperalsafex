import logging
import time
from pathlib import Path

import requests

from . import config

logger = logging.getLogger(__name__)


def upload(path: Path = config.OUTPUT_FILE) -> bool:
    if not config.KNOWLEDGE_ENDPOINT:
        logger.info("ALSAFEX_KNOWLEDGE_ENDPOINT no configurado; se omite la subida")
        return False
    if not config.KNOWLEDGE_TOKEN:
        logger.error("Falta ALSAFEX_KNOWLEDGE_TOKEN; no se sube el JSON")
        return False

    headers = {
        "X-Knowledge-Token": config.KNOWLEDGE_TOKEN,
        "Content-Type": "application/json",
    }
    body = path.read_bytes()
    last_error: Exception | None = None

    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            response = requests.post(
                config.KNOWLEDGE_ENDPOINT,
                headers=headers,
                data=body,
                timeout=config.REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            logger.info("Import enviado (HTTP %s)", response.status_code)
            return True
        except requests.RequestException as exc:
            last_error = exc
            logger.warning("Subida fallida %s/%s: %s", attempt, config.MAX_RETRIES, exc)
            if attempt < config.MAX_RETRIES:
                time.sleep(config.RETRY_BACKOFF ** attempt)

    raise RuntimeError("No se pudo subir el knowledge.json") from last_error
