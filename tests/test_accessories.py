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

    def test_parse_accessories_generates_unique_keys_for_same_title(self):
        products = [
            {
                "id": 201,
                "name": "Cierre multipunto",
                "permalink": "https://alsafex.com.ar/producto/cierre-multipunto-a/",
                "categories": [{"name": "Accesorios"}, {"name": "Herrajes"}],
            },
            {
                "id": 202,
                "name": "Cierre multipunto",
                "permalink": "https://alsafex.com.ar/producto/cierre-multipunto-b/",
                "categories": [{"name": "Accesorios"}, {"name": "Herrajes"}],
            },
        ]

        result = parse_accessories(products)

        self.assertEqual(len(result), 2)
        self.assertNotEqual(result[0].doc_key, result[1].doc_key)

    def test_parse_accessories_removes_description_prefix(self):
        products = [
            {
                "id": 203,
                "name": "Bisagra",
                "permalink": "https://alsafex.com.ar/producto/bisagra/",
                "description": "<ul><li><strong>Descripción:</strong> Bisagra para línea corrediza</li></ul>",
                "categories": [{"name": "Accesorios"}, {"name": "Herrajes"}],
            }
        ]

        result = parse_accessories(products)

        self.assertEqual(result[0].description, "Bisagra para línea corrediza")

    def test_parse_accessories_excludes_single_accessories_category(self):
        products = [
            {
                "id": 301,
                "name": "Producto excluido",
                "permalink": "https://alsafex.com.ar/producto/producto-excluido/",
                "categories": [{"name": "Accesorios"}],
            },
            {
                "id": 302,
                "name": "Producto incluido",
                "permalink": "https://alsafex.com.ar/producto/producto-incluido/",
                "categories": [{"name": "Accesorios"}, {"name": "Herrajes"}],
            },
        ]

        result = parse_accessories(products)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Producto incluido")

    def test_parse_accessories_excludes_products_without_valid_categories(self):
        products = [
            {
                "id": 401,
                "name": "Sin categoria",
                "permalink": "https://alsafex.com.ar/producto/sin-categoria/",
                "categories": [],
            }
        ]

        result = parse_accessories(products)

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
