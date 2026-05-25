import grpc
from typing import List

from app.grpc_client import producto_pb2, producto_pb2_grpc
from app.schemas.producto_schema import ProductoType, ProductoInput

GRPC_HOST = "localhost:50051"


def _respuesta_a_type(r) -> ProductoType:
    return ProductoType(
        id=r.id,
        nombre=r.nombre,
        descripcion=r.descripcion if r.descripcion else None,
        precio=r.precio,
    )


def crear_producto_grpc(data: ProductoInput) -> ProductoType:
    channel = grpc.insecure_channel(GRPC_HOST)
    try:
        stub = producto_pb2_grpc.ProductoServiceStub(channel)
        request = producto_pb2.ProductoRequest(
            nombre=data.nombre,
            descripcion=data.descripcion or "",
            precio=data.precio,
        )
        response = stub.CreateProducto(request)
        return _respuesta_a_type(response)
    except grpc.RpcError as e:
        raise Exception(f"Error gRPC [{e.code()}]: {e.details()}")
    finally:
        channel.close()


def listar_productos_grpc() -> List[ProductoType]:
    channel = grpc.insecure_channel(GRPC_HOST)
    try:
        stub = producto_pb2_grpc.ProductoServiceStub(channel)
        response = stub.ListProductos(producto_pb2.Empty())
        return [_respuesta_a_type(p) for p in response.productos]
    except grpc.RpcError as e:
        raise Exception(f"Error gRPC [{e.code()}]: {e.details()}")
    finally:
        channel.close()
