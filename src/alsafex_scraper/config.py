import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

SOURCE_URL = os.getenv("ALSAFEX_URL", "https://alsafex.com.ar/descargas")

OUTPUT_DIR = Path(os.getenv("ALSAFEX_OUTPUT_DIR", BASE_DIR / "output"))
OUTPUT_FILE = Path(os.getenv("ALSAFEX_OUTPUT_FILE", OUTPUT_DIR / "knowledge.json"))
LOG_DIR = Path(os.getenv("ALSAFEX_LOG_DIR", BASE_DIR / "logs"))

KNOWLEDGE_ENDPOINT = os.getenv("ALSAFEX_KNOWLEDGE_ENDPOINT", "").strip()
KNOWLEDGE_TOKEN = os.getenv("ALSAFEX_KNOWLEDGE_TOKEN", "").strip()
UPLOAD_ENABLED = os.getenv("ALSAFEX_UPLOAD", "true").lower() == "true"

REQUEST_TIMEOUT = int(os.getenv("ALSAFEX_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("ALSAFEX_MAX_RETRIES", "3"))
RETRY_BACKOFF = float(os.getenv("ALSAFEX_RETRY_BACKOFF", "2"))

USER_AGENT = os.getenv(
    "ALSAFEX_USER_AGENT",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
)

# Solo se aceptan PDFs servidos por este host, para evitar seguir enlaces externos.
ALLOWED_HOST = "alsafex.com.ar"

# Cortafuegos ante un cambio de maquetación: si se extraen muy pocos documentos se
# aborta la subida, porque el import reemplaza todo el contenido del asistente.
MIN_DOCUMENTS = int(os.getenv("ALSAFEX_MIN_DOCUMENTS", "40"))

# El encabezado de cada sección se normaliza y se busca por palabras clave, porque
# los IDs de Elementor cambian cada vez que se edita la página.
CATEGORY_RULES = [
    ("catalogos_perfiles", "Catálogos de Perfiles", ("catalogo", "perfil")),
    ("manuales_mecanizado", "Manuales de Mecanizado", ("manual", "mecanizado")),
    ("manuales_lineas", "Manuales de Líneas", ("manual", "linea")),
    ("boletines_tecnicos", "Boletines Técnicos", ("boletin",)),
    ("brochures_comerciales", "Brochures Comerciales y Accesorios", ("brochure",)),
]
