import unittest

from alsafex_scraper.knowledge import build_payload
from alsafex_scraper.scraper import Document


class KnowledgePayloadTest(unittest.TestCase):
    def test_build_payload_splits_documents_and_accessories(self):
        docs = [
            Document(
                category_slug="catalogos_perfiles",
                category="Catálogos de Perfiles",
                name="Catalogo Serie A",
                url="https://alsafex.com.ar/wp-content/uploads/2024/01/catalogo-a.pdf",
                file_date="2024-01",
                doc_key="doc-001",
            ),
            Document(
                category_slug="accesorios",
                category="Herrajes, Accesorios",
                name="Bisagra reforzada",
                url="https://alsafex.com.ar/producto/bisagra-reforzada/",
                file_date=None,
                doc_key="acc-001",
                description="Accesorio para linea corrediza",
            ),
        ]

        payload = build_payload(docs)

        self.assertEqual(payload["total"], 2)
        self.assertEqual(len(payload["documentos"]), 1)
        self.assertEqual(len(payload["accesorios"]), 1)
        self.assertEqual(payload["documentos"][0]["categoria_slug"], "catalogos_perfiles")
        self.assertEqual(payload["accesorios"][0]["categoria_slug"], "accesorios")
        self.assertIn("descripcion", payload["accesorios"][0])
        self.assertNotIn("categorias", payload)


if __name__ == "__main__":
    unittest.main()
