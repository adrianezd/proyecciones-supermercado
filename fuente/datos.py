"""
Descarga de precios de supermercado de Open Prices (Open Food Facts).

Proyecto colaborativo: los precios los suben los propios compradores con
foto del ticket, asi que la cobertura en España es irregular. No existe
ninguna API oficial de precios de Mercadona, Carrefour o Dia, y raspar sus
webs seria fragil y juridicamente turbio. Licencia OdBL: hay que citar la
fuente.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

CACHE = Path(__file__).parent.parent / "cache"
CACHE.mkdir(exist_ok=True)

CABECERAS = {
    "User-Agent": "proyecciones-supermercado/1.0 (+https://github.com/adrianezd/proyecciones-supermercado)",
    "Accept": "application/json, text/plain, */*",
}

OPEN_PRICES = "https://prices.openfoodfacts.org/api/v1/prices"


def _descargar(url: str, clave: str, params: dict | None = None) -> Any:
    fichero = CACHE / f"{clave}.json"
    try:
        r = httpx.get(url, params=params, headers=CABECERAS,
                      timeout=40.0, follow_redirects=True)
        r.raise_for_status()
        datos = r.json()
        fichero.write_text(json.dumps(datos), encoding="utf-8")
        print(f"  descargado  {clave}")
        return datos
    except Exception as e:
        if fichero.exists():
            print(f"  CACHE       {clave}  ({type(e).__name__})")
            return json.loads(fichero.read_text(encoding="utf-8"))
        print(f"  FALLO       {clave}  ({e})")
        return None


def precios_supermercado(paginas: int = 6) -> list[dict]:
    """Ultimos precios en euros registrados en tiendas de España."""
    todo = []

    for pagina in range(1, paginas + 1):
        datos = _descargar(OPEN_PRICES, f"precios-{pagina}", {
            "currency": "EUR",
            "order_by": "-created",
            "size": 100,
            "page": pagina,
        })
        if not isinstance(datos, dict):
            break

        items = datos.get("items") or []
        if not items:
            break
        todo.extend(items)

    salida = []
    for it in todo:
        precio = it.get("price")
        if not isinstance(precio, (int, float)) or precio <= 0:
            continue

        lugar = it.get("location") or {}
        pais = (lugar.get("osm_address_country_code")
                or lugar.get("osm_address_country") or "")
        if pais and str(pais).lower() not in ("es", "spain", "españa"):
            continue

        producto = it.get("product") or {}
        nombre = (producto.get("product_name")
                  or it.get("product_code")
                  or it.get("category_tag") or "")
        if not nombre:
            continue

        salida.append({
            "producto": str(nombre)[:70],
            "precio": round(float(precio), 2),
            "tienda": (lugar.get("osm_name") or "Tienda sin identificar")[:40],
            "ciudad": (lugar.get("osm_address_city") or "")[:40],
            "fecha": it.get("date") or "",
        })

    return salida
