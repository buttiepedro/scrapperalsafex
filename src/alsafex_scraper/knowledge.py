import json
import logging
from pathlib import Path

from . import config
from .scraper import Document, utc_now

logger = logging.getLogger(__name__)


def build_payload(documents: list[Document]) -> dict:
    regular_documents = [doc for doc in documents if doc.category_slug != "accesorios"]
    accessories = [doc for doc in documents if doc.category_slug == "accesorios"]

    return {
        "fuente": config.SOURCE_URL,
        "generado_en": utc_now(),
        "total": len(documents),
        "documentos": [
            {
                "id": doc.doc_key,
                "titulo": doc.name,
                "categoria": doc.category,
                "categoria_slug": doc.category_slug,
                "url": doc.url,
                "fecha_publicacion": doc.file_date,
                **({"descripcion": doc.description} if doc.description else {}),
            }
            for doc in regular_documents
        ],
        "accesorios": [
            {
                "id": doc.doc_key,
                "titulo": doc.name,
                "categoria": doc.category,
                "categoria_slug": doc.category_slug,
                "url": doc.url,
                "fecha_publicacion": doc.file_date,
                **({"descripcion": doc.description} if doc.description else {}),
            }
            for doc in accessories
        ],
    }


def write_payload(payload: dict, path: Path = config.OUTPUT_FILE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Escritura atómica para que nunca quede un JSON a medias si el proceso se corta.
    temporary = path.with_suffix(path.suffix + ".tmp")
    # Cada corrida regenera el archivo desde cero; no se reutiliza contenido previo.
    if temporary.exists():
        temporary.unlink()
    if path.exists():
        path.unlink()
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
    logger.info("JSON generado en %s (%s items)", path, payload["total"])
    return path
