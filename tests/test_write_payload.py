import json
import tempfile
import unittest
from pathlib import Path

from alsafex_scraper.knowledge import write_payload


class WritePayloadTest(unittest.TestCase):
    def test_write_payload_recreates_file_from_scratch(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "knowledge.json"
            target.write_text("old-content-that-must-disappear", encoding="utf-8")

            payload = {
                "fuente": "https://alsafex.com.ar/descargas",
                "generado_en": "2026-08-19T00:00:00+00:00",
                "total": 1,
                "documentos": [],
                "accesorios": [
                    {
                        "id": "abc123",
                        "titulo": "Bisagra",
                        "categoria": "Accesorios",
                        "categoria_slug": "accesorios",
                        "url": "https://alsafex.com.ar/producto/bisagra/",
                        "fecha_publicacion": None,
                    }
                ],
            }

            write_payload(payload, path=target)

            loaded = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(loaded, payload)


if __name__ == "__main__":
    unittest.main()
