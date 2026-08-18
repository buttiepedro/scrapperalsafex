# scrapperalsafex

Scraper de la sección [Descargas de Alsafex](https://alsafex.com.ar/descargas). Genera un
`knowledge.json` y lo sube al endpoint de la base de conocimiento del asistente. Corre todos
los días a las **00:00 (America/Argentina/Buenos_Aires)**.

Reemplaza a los 5 workflows de n8n (uno por categoría) con una sola ejecución.

## Qué extrae

| Categoría | Slug | Documentos |
|---|---|---|
| Catálogos de Perfiles | `catalogos_perfiles` | 12 |
| Manuales de Líneas | `manuales_lineas` | 14 |
| Manuales de Mecanizado | `manuales_mecanizado` | 3 |
| Boletines Técnicos | `boletines_tecnicos` | 18 |
| Brochures Comerciales y Accesorios | `brochures_comerciales` | 11 |

A diferencia de n8n, no se usan los IDs de Elementor (`.elementor-element-91ebc14`), que cambian
al editar la página. Las categorías se detectan por el texto del encabezado, y el nombre y la URL
se leen del mismo `<a>`, así que no hay emparejado por índice que se pueda desalinear.

## Uso local

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env    # completar el token

# Solo generar el JSON, sin subirlo
PYTHONPATH=src python -m alsafex_scraper.main --no-upload

# Generar y subir
PYTHONPATH=src python -m alsafex_scraper.main
```

El resultado queda en `output/knowledge.json` y los logs en `logs/`.

## Deploy en el servidor

```bash
git clone https://github.com/buttiepedro/scrapperalsafex.git
cd scrapperalsafex
cp .env.example .env    # completar ALSAFEX_KNOWLEDGE_TOKEN

docker compose up -d --build
docker compose logs -f
```

El contenedor deja un `cron` corriendo y ejecuta el scraper a las 00:00. Para forzar una
ejecución inmediata:

```bash
docker compose exec alsafex-scraper python -m alsafex_scraper.main
```

## Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `ALSAFEX_KNOWLEDGE_ENDPOINT` | — | URL del `POST /knowledge/import` |
| `ALSAFEX_KNOWLEDGE_TOKEN` | — | Valor del header `X-Knowledge-Token` |
| `ALSAFEX_URL` | `https://alsafex.com.ar/descargas` | Página origen |
| `ALSAFEX_UPLOAD` | `true` | `false` para solo generar el JSON |
| `ALSAFEX_MIN_DOCUMENTS` | `40` | Mínimo para permitir la subida |
| `ALSAFEX_TIMEOUT` | `30` | Timeout HTTP en segundos |
| `ALSAFEX_MAX_RETRIES` | `3` | Reintentos ante fallos de red |

Como cada import **reemplaza todo** el contenido, si el scraper extrae menos de
`ALSAFEX_MIN_DOCUMENTS` documentos aborta sin subir nada. Así un cambio de maquetación no
deja la base de conocimiento vacía.

## Formato del JSON

```json
{
  "fuente": "https://alsafex.com.ar/descargas",
  "generado_en": "2026-08-18T18:24:31+00:00",
  "total": 58,
  "categorias": [
    {
      "slug": "catalogos_perfiles",
      "nombre": "Catálogos de Perfiles",
      "documentos": [
        { "nombre": "Alfa", "url": "https://...pdf", "fecha_publicacion": "2023-08" }
      ]
    }
  ],
  "items": [
    {
      "id": "a1b2c3d4e5f6a7b8",
      "titulo": "Alfa",
      "categoria": "Catálogos de Perfiles",
      "categoria_slug": "catalogos_perfiles",
      "url": "https://...pdf",
      "fecha_publicacion": "2023-08",
      "contenido": "Alfa es un documento de la categoría..."
    }
  ]
}
```

El esquema se arma en `src/alsafex_scraper/knowledge.py`; si el backend espera otra forma,
se ajusta solo ahí.

