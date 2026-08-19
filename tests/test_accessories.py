import unittest

from alsafex_scraper.scraper import parse_accessories


class AccessoriesParsingTest(unittest.TestCase):
    def test_parse_accessories_extracts_clean_name_and_categories(self):
        products = [
            {
                "id": 101,
                "name": "Llave de impacto",
                "permalink": "https://alsafex.com.ar/producto/llave-de-impacto/",
                "description": "<p>Llave <strong>de</strong> impacto</p><p>Ideal para uso profesional.</p>",
                "categories": [
                    {"name": "Herramientas"},
                    {"name": "Accesorios"},
                ],
            }
        ]

        result = parse_accessories(products)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Llave de impacto")
        self.assertEqual(result[0].category, "Herramientas, Accesorios")
        self.assertEqual(result[0].category_slug, "accesorios")
        self.assertIn("llave-de-impacto", result[0].url or "")
        self.assertIn("Ideal para uso profesional", result[0].description)


if __name__ == "__main__":
    unittest.main()
