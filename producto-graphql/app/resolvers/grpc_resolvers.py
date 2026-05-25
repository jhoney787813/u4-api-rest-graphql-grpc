from typing import List

from app.schemas.producto_schema import ProductoType, ProductoInput
from app.grpc_client.client import crear_producto_grpc, listar_productos_grpc


def resolver_crear_producto_grpc(data: ProductoInput) -> ProductoType:
    return crear_producto_grpc(data)


def resolver_listar_productos_grpc() -> List[ProductoType]:
    return listar_productos_grpc()
