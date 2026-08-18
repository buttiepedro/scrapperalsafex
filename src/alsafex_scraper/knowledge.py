import json
import logging
from pathlib import Path

from . import config
from .scraper import Document, utc_now

logger = logging.getLogger(__name__)


def build_payload(documents: list[Document]) -> dict:
    categories: dict[str, dict] = {}
    for doc in documents:
        bucket = categories.setdefault(
            doc.category_slug,
            {"slug": doc.category_slug, "nombre": doc.category, "cantidad": 0},
        )
        bucket["cantidad"] += 1

    return {
        "fuente": config.SOURCE_URL,
        "generado_en": utc_now(),
        "total": len(documents),
        "categorias": list(categories.values()),
        "documentos": [
            {
                "id": doc.doc_key,
                "titulo": doc.name,
                "categoria": doc.category,
                "categoria_slug": doc.category_slug,
                "url": doc.url,
                "fecha_publicacion": doc.file_date,
            }
            for doc in documents
        ],
    }


def write_payload(payload: dict, path: Path = config.OUTPUT_FILE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Escritura atómica para que nunca quede un JSON a medias si el proceso se corta.
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
    logger.info("JSON generado en %s (%s items)", path, payload["total"])
    return path
