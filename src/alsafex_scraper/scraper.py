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
    description: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


def _strip_html(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"<[^>]+>", " ", value)


def _clean_description(value: str | None) -> str:
    cleaned = _strip_html(value).replace("\xa0", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


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


def _doc_key(category_slug: str, name: str, unique_hint: str | None = None) -> str:
    raw = f"{category_slug}|{_normalize(name)}"
    if unique_hint:
        raw += f"|{_normalize(unique_hint)}"
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


def fetch_json_paginated(url: str, *, params: dict | None = None) -> list[dict]:
    headers = {"User-Agent": config.USER_AGENT, "Accept-Language": "es-AR,es;q=0.9"}
    merged_params = {"per_page": config.ACCESSORIES_PER_PAGE, **(params or {})}
    collected: list[dict] = []
    page = 1
    last_error: Exception | None = None

    while page <= config.ACCESSORIES_MAX_PAGES:
        request_params = {**merged_params, "page": page}
        try:
            response = requests.get(
                url,
                params=request_params,
                headers=headers,
                timeout=config.REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()
            if not payload:
                break
            if not isinstance(payload, list):
                raise ValueError(f"La API respondió un payload inesperado en {url}: {type(payload).__name__}")
            collected.extend(payload)
            if len(payload) < request_params["per_page"]:
                break
            page += 1
        except requests.RequestException as exc:
            last_error = exc
            logger.warning("Fallo al consultar accesorios en %s (página %s): %s", url, page, exc)
            break
        except ValueError as exc:
            last_error = exc
            logger.warning("Respuesta inválida de accesorios en %s: %s", url, exc)
            break

    if last_error is not None and not collected:
        raise RuntimeError(f"No se pudo consultar {url}") from last_error

    return collected


def parse_accessories(products: list[dict]) -> list[Document]:
    parsed: list[Document] = []
    seen_urls: set[str] = set()
    for product in products:
        categories = product.get("categories") or []
        valid_categories = [
            category
            for category in categories
            if isinstance(category, dict) and category.get("name")
        ]
        # Se excluyen productos sin categorias utiles y los que solo tienen "Accesorios".
        if not valid_categories:
            continue
        if len(valid_categories) == 1 and _normalize(valid_categories[0].get("name", "")) == "accesorios":
            continue

        category_names = ", ".join(category.get("name", "") for category in valid_categories)

        description = _clean_description(product.get("description") or product.get("short_description"))
        name = _clean(product.get("name") or "Producto")
        url = product.get("permalink") or ""
        if not url:
            url = f"https://alsafex.com.ar/producto/{_normalize(name).replace(' ', '-')}/"
        if url in seen_urls:
            continue

        seen_urls.add(url)
        product_id = product.get("id")

        parsed.append(
            Document(
                category_slug="accesorios",
                category=category_names,
                name=name,
                url=url,
                file_date=None,
                doc_key=_doc_key("accesorios", name, unique_hint=str(product_id or url)),
                description=description,
            )
        )
    return parsed


def fetch_accessory_categories() -> list[dict]:
    logger.info("Consultando categorías de accesorios desde %s", config.ACCESSORIES_CATEGORIES_URL)
    categories = fetch_json_paginated(config.ACCESSORIES_CATEGORIES_URL)
    return [
        {
            "id": item.get("id"),
            "nombre": item.get("name"),
            "permalink": item.get("permalink"),
        }
        for item in categories
        if isinstance(item, dict)
    ]


def scrape_accessories() -> list[Document]:
    logger.info("Consultando accesorios desde %s", config.ACCESSORIES_URL)
    products = fetch_json_paginated(config.ACCESSORIES_URL)
    documents = parse_accessories(products)
    logger.info("Se encontraron %s productos de accesorios", len(documents))
    return documents


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
