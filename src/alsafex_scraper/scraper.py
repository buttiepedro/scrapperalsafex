import hashlib
import logging
import re
import time
import unicodedata
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from . import config

logger = logging.getLogger(__name__)

HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")
UPLOAD_DATE_RE = re.compile(r"/uploads/(\d{4})/(\d{2})/")


@dataclass(frozen=True)
class Document:
    category_slug: str
    category: str
    name: str
    url: str
    file_date: str | None
    doc_key: str

    def as_dict(self) -> dict:
        return asdict(self)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip().lower()


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _match_category(heading: str) -> tuple[str, str] | None:
    normalized = _normalize(heading)
    for slug, label, keywords in config.CATEGORY_RULES:
        if all(keyword in normalized for keyword in keywords):
            return slug, label
    return None


def _file_date(url: str) -> str | None:
    match = UPLOAD_DATE_RE.search(url)
    return f"{match.group(1)}-{match.group(2)}" if match else None


def _doc_key(category_slug: str, name: str) -> str:
    raw = f"{category_slug}|{_normalize(name)}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def fetch_html(url: str = config.SOURCE_URL) -> str:
    headers = {"User-Agent": config.USER_AGENT, "Accept-Language": "es-AR,es;q=0.9"}
    last_error: Exception | None = None

    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"
            return response.text
        except requests.RequestException as exc:
            last_error = exc
            logger.warning("Intento %s/%s falló: %s", attempt, config.MAX_RETRIES, exc)
            if attempt < config.MAX_RETRIES:
                time.sleep(config.RETRY_BACKOFF ** attempt)

    raise RuntimeError(f"No se pudo descargar {url}") from last_error


def parse_documents(html: str, base_url: str = config.SOURCE_URL) -> list[Document]:
    soup = BeautifulSoup(html, "lxml")
    root = soup.find("main") or soup.body or soup

    documents: list[Document] = []
    seen_urls: set[str] = set()
    current: tuple[str, str] | None = None

    # Se recorre el documento en orden para asignar cada PDF al último encabezado visto.
    for node in root.find_all([*HEADING_TAGS, "a"]):
        if node.name in HEADING_TAGS:
            heading = _clean(node.get_text(" ", strip=True))
            if heading:
                matched = _match_category(heading)
                if matched:
                    current = matched
            continue

        href = node.get("href", "")
        if not href:
            continue

        url = urljoin(base_url, href.strip())
        parsed = urlparse(url)
        if not parsed.path.lower().endswith(".pdf"):
            continue
        if parsed.hostname is None or not parsed.hostname.endswith(config.ALLOWED_HOST):
            continue
        if current is None or url in seen_urls:
            continue

        label = node.select_one(".elementor-icon-list-text")
        name = _clean(label.get_text(" ", strip=True) if label else node.get_text(" ", strip=True))
        if not name:
            name = parsed.path.rsplit("/", 1)[-1].removesuffix(".pdf").replace("-", " ")

        seen_urls.add(url)
        slug, category = current
        documents.append(
            Document(
                category_slug=slug,
                category=category,
                name=name,
                url=url,
                file_date=_file_date(url),
                doc_key=_doc_key(slug, name),
            )
        )

    return documents


def scrape(url: str = config.SOURCE_URL) -> list[Document]:
    logger.info("Descargando %s", url)
    documents = parse_documents(fetch_html(url), url)
    logger.info("Se encontraron %s documentos", len(documents))
    if not documents:
        raise RuntimeError("No se encontró ningún documento; la página pudo haber cambiado")
    return documents


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
