import grpc
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.producto import Producto
from app.core.exceptions import (
    GrpcError, handle_grpc_error,
    not_found_error, invalid_argument_error, internal_error,
)
from app.protos import producto_pb2, producto_pb2_grpc
from app.graphql_client.client import listar_productos_graphql


def _modelo_a_response(p: Producto) -> producto_pb2.ProductoResponse:
    """Convierte un modelo SQLAlchemy Producto a ProductoResponse protobuf."""
    return producto_pb2.ProductoResponse(
        id=p.id,
        nombre=p.nombre,
        descripcion=p.descripcion or "",
        precio=p.precio,
    )


def _validar_nombre(nombre: str) -> None:
    if not nombre or not nombre.strip():
        raise invalid_argument_error("El nombre no puede estar vacío")


def _validar_precio(precio: float) -> None:
    if precio < 0:
        raise invalid_argument_error("El precio debe ser mayor o igual a 0")


class ProductoServicer(producto_pb2_grpc.ProductoServiceServicer):
    """Implementación del servicio gRPC ProductoService."""

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------
    def CreateProducto(self, request, context):
        db: Session = SessionLocal()
        try:
            _validar_nombre(request.nombre)
            _validar_precio(request.precio)

            producto = Producto(
                nombre=request.nombre.strip(),
                descripcion=request.descripcion if request.descripcion else None,
                precio=request.precio,
            )
            db.add(producto)
            db.commit()
            db.refresh(producto)
            return _modelo_a_response(producto)

        except GrpcError as e:
            handle_grpc_error(context, e)
            return producto_pb2.ProductoResponse()
        except Exception as e:
            handle_grpc_error(context, internal_error(str(e)))
            return producto_pb2.ProductoResponse()
        finally:
            db.close()

    # ------------------------------------------------------------------
    # LIST
    # ------------------------------------------------------------------
    def ListProductos(self, request, context):
        db: Session = SessionLocal()
        try:
            productos = db.query(Producto).all()
            return producto_pb2.ProductoList(
                productos=[_modelo_a_response(p) for p in productos]
            )
        except Exception as e:
            handle_grpc_error(context, internal_error(str(e)))
            return producto_pb2.ProductoList()
        finally:
            db.close()

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------
    def GetProducto(self, request, context):
        db: Session = SessionLocal()
        try:
            producto = db.query(Producto).filter(Producto.id == request.id).first()
            if not producto:
                raise not_found_error(request.id)
            return _modelo_a_response(producto)

        except GrpcError as e:
            handle_grpc_error(context, e)
            return producto_pb2.ProductoResponse()
        except Exception as e:
            handle_grpc_error(context, internal_error(str(e)))
            return producto_pb2.ProductoResponse()
        finally:
            db.close()

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    def UpdateProducto(self, request, context):
        db: Session = SessionLocal()
        try:
            producto = db.query(Producto).filter(Producto.id == request.id).first()
            if not producto:
                raise not_found_error(request.id)

            if request.update_nombre:
                _validar_nombre(request.nombre)
                producto.nombre = request.nombre.strip()

            if request.update_descripcion:
                producto.descripcion = request.descripcion if request.descripcion else None

            if request.update_precio:
                _validar_precio(request.precio)
                producto.precio = request.precio

            db.commit()
            db.refresh(producto)
            return _modelo_a_response(producto)

        except GrpcError as e:
            handle_grpc_error(context, e)
            return producto_pb2.ProductoResponse()
        except Exception as e:
            handle_grpc_error(context, internal_error(str(e)))
            return producto_pb2.ProductoResponse()
        finally:
            db.close()

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    def DeleteProducto(self, request, context):
        db: Session = SessionLocal()
        try:
            producto = db.query(Producto).filter(Producto.id == request.id).first()
            if not producto:
                raise not_found_error(request.id)

            db.delete(producto)
            db.commit()
            return producto_pb2.DeleteResponse(
                success=True,
                message=f"Producto {request.id} eliminado exitosamente",
            )

        except GrpcError as e:
            handle_grpc_error(context, e)
            return producto_pb2.DeleteResponse(success=False, message=e.message)
        except Exception as e:
            handle_grpc_error(context, internal_error(str(e)))
            return producto_pb2.DeleteResponse(success=False, message=str(e))
        finally:
            db.close()

    # ------------------------------------------------------------------
    # LIST PRODUCTOS GRAPHQL (consulta el API GraphQL — tabla productosgraphql)
    # ------------------------------------------------------------------
    def ListProductosGraphQL(self, request, context):
        try:
            productos = listar_productos_graphql()
            return producto_pb2.ProductoList(
                productos=[
                    producto_pb2.ProductoResponse(
                        id=p["id"],
                        nombre=p["nombre"],
                        descripcion=p.get("descripcion") or "",
                        precio=p["precio"],
                    )
                    for p in productos
                ]
            )
        except ConnectionError as e:
            handle_grpc_error(context, internal_error(str(e)))
            return producto_pb2.ProductoList()
        except Exception as e:
            handle_grpc_error(context, internal_error(str(e)))
            return producto_pb2.ProductoList()
