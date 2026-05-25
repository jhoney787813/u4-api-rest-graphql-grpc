import json
import urllib.request
import urllib.error
from typing import List

GRAPHQL_URL = "http://localhost:8000/graphql"

_QUERY_LISTAR = """
query {
  productos {
    id
    nombre
    descripcion
    precio
  }
}
"""


def listar_productos_graphql() -> List[dict]:
    """Llama al endpoint GraphQL /graphql y retorna la lista de productos (tabla productosgraphql)."""
    payload = json.dumps({"query": _QUERY_LISTAR}).encode("utf-8")
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise ConnectionError(
            f"No se pudo conectar al servidor GraphQL en {GRAPHQL_URL}: {e.reason}"
        )

    if "errors" in data:
        raise RuntimeError(f"Error desde GraphQL: {data['errors']}")

    return data["data"]["productos"]
