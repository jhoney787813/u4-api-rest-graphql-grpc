import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app.database import engine, Base, get_db
from app.schemas.producto_schema import ProductoType, ProductoInput, ProductoUpdateInput
from app.resolvers.queries import get_productos, get_producto
from app.resolvers.mutations import crear_producto, actualizar_producto, eliminar_producto
from app.resolvers.grpc_resolvers import resolver_crear_producto_grpc, resolver_listar_productos_grpc
from app.core.exceptions import ProductoNotFoundError, ValidationError

Base.metadata.create_all(bind=engine)

async def get_context_db() -> dict:
    db = next(get_db())
    return {"db": db}

@strawberry.type
class Query:
    @strawberry.field
    def productos(self, info: Info[Any, None]) -> List[ProductoType]:
        db: Session = info.context["db"]
        return get_productos(db)

    @strawberry.field
    def producto(self, info: Info[Any, None], id: int) -> Optional[ProductoType]:
        db: Session = info.context["db"]
        try:
            return get_producto(db, id)
        except ProductoNotFoundError as e:
            raise Exception(e.message)

    @strawberry.field
    def productos_grpc(self, info: Info[Any, None]) -> List[ProductoType]:
        """Lista productos consultando directamente el servicio gRPC (tabla productosgrpc)."""
        try:
            return resolver_listar_productos_grpc()
        except Exception as e:
            raise Exception(str(e))

@strawberry.type
class Mutation:
    @strawberry.mutation
    def crear_producto(self, info: Info[Any, None], data: ProductoInput) -> ProductoType:
        db: Session = info.context["db"]
        try:
            return crear_producto(db, data)
        except (ValidationError, ProductoNotFoundError) as e:
            raise Exception(e.message)

    @strawberry.mutation
    def actualizar_producto(self, info: Info[Any, None], id: int, data: ProductoUpdateInput) -> ProductoType:
        db: Session = info.context["db"]
        try:
            return actualizar_producto(db, id, data)
        except (ValidationError, ProductoNotFoundError) as e:
            raise Exception(e.message)

    @strawberry.mutation
    def eliminar_producto(self, info: Info[Any, None], id: int) -> bool:
        db: Session = info.context["db"]
        try:
            return eliminar_producto(db, id)
        except ProductoNotFoundError as e:
            raise Exception(e.message)

    @strawberry.mutation
    def crear_producto_grpc(self, info: Info[Any, None], data: ProductoInput) -> ProductoType:
        """Inserta un producto llamando al servicio gRPC (escribe en tabla productosgrpc)."""
        try:
            return resolver_crear_producto_grpc(data)
        except Exception as e:
            raise Exception(str(e))

schema = strawberry.Schema(query=Query, mutation=Mutation)

graphql_app = GraphQLRouter(schema, context_getter=get_context_db)

app = FastAPI(title="API GraphQL Productos", version="1.0.0")
app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
def root():
    return {"message": "API GraphQL Productos - Ir a /graphql"}
