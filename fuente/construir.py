"""
Generador de esta pagina: precios de supermercado en España.

    python -m fuente.construir
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import calculo, datos
from .enlaces import HUB, MENU

AQUI = Path(__file__).parent
PROYECTO = AQUI.parent
SALIDA = PROYECTO / "docs"

BASE_URL = "https://adrianezd.github.io/proyecciones-supermercado"

entorno = Environment(
    loader=FileSystemLoader(AQUI / "plantillas"),
    autoescape=select_autoescape(["html"]),
)

HOY = dt.date.today().isoformat()


def json_seguro(obj) -> str:
    texto = json.dumps(obj, ensure_ascii=False)
    return (texto
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026")
            .replace(" ", "\\u2028")
            .replace(" ", "\\u2029"))


def escribir(plantilla: str, **contexto) -> None:
    destino = SALIDA / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)

    contexto.setdefault("raiz", "./")
    contexto.setdefault("menu", MENU)
    contexto.setdefault("hub", HUB)
    contexto.setdefault("base_url", BASE_URL)
    contexto.setdefault("ruta", "")
    contexto.setdefault("generado", HOY)

    destino.write_text(entorno.get_template(plantilla).render(**contexto), encoding="utf-8")
    print("  escrito     index.html")


def main() -> None:
    print("Construyendo: supermercado\n")

    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    SALIDA.mkdir(parents=True)
    shutil.copytree(PROYECTO / "estatico", SALIDA / "estatico")

    precios = datos.precios_supermercado()
    if len(precios) < 10:
        print(f"  SALTADA     supermercado (solo {len(precios)} registros españoles)")
        (SALIDA / ".nojekyll").write_text("", encoding="utf-8")
        return

    valores = sorted(p["precio"] for p in precios)
    por_tienda: dict[str, int] = {}
    for p in precios:
        por_tienda[p["tienda"]] = por_tienda.get(p["tienda"], 0) + 1

    top = sorted(por_tienda.items(), key=lambda x: -x[1])[:12]

    escribir(
        "supermercado.html",
        acento="supermercado",
        titulo="Precios de supermercado en España",
        descripcion="Precios reales de productos en tiendas españolas recogidos "
                    "por Open Prices, la base colaborativa de Open Food Facts.",
        total=len(precios),
        tiendas=len(por_tienda),
        ultimos=precios[:25],
        datos_json=json_seguro({
            "hist": calculo.histograma(valores, 20),
            "tiendas": [{"nombre": n, "cuantos": c} for n, c in top],
        }),
    )

    (SALIDA / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8"
    )
    (SALIDA / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f'\n  <url><loc>{BASE_URL}/</loc><lastmod>{HOY}</lastmod></url>\n</urlset>\n',
        encoding="utf-8",
    )
    (SALIDA / ".nojekyll").write_text("", encoding="utf-8")

    print("\nListo.")


if __name__ == "__main__":
    main()
