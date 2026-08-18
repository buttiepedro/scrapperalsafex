import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler

from . import config, knowledge, uploader
from .scraper import scrape

logger = logging.getLogger("alsafex_scraper")


def setup_logging(verbose: bool = False) -> None:
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(
            config.LOG_DIR / "scraper.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8"
        ),
    ]
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        handlers=handlers,
    )


def run(upload: bool = True) -> int:
    try:
        documents = scrape()

        if len(documents) < config.MIN_DOCUMENTS:
            raise RuntimeError(
                f"Solo se extrajeron {len(documents)} documentos "
                f"(mínimo {config.MIN_DOCUMENTS}); se aborta para no vaciar la base"
            )

        payload = knowledge.build_payload(documents)
        path = knowledge.write_payload(payload)

        for category in payload["categorias"]:
            logger.info("%-34s %s", category["nombre"], len(category["documentos"]))

        if upload and config.UPLOAD_ENABLED:
            uploader.upload(path)
        else:
            logger.info("Subida desactivada; el JSON quedó en %s", path)

        return 0
    except Exception:
        logger.exception("La ejecución falló")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Scraper de descargas de Alsafex")
    parser.add_argument(
        "--no-upload", action="store_true", help="solo generar el JSON, sin enviarlo"
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    setup_logging(args.verbose)
    return run(upload=not args.no_upload)


if __name__ == "__main__":
    raise SystemExit(main())
