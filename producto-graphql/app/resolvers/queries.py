import strawberry
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.producto import Producto as ProductoModel
from app.schemas.producto_schema import ProductoType
from app.core.exceptions import ProductoNotFoundError

def get_productos(db: Session) -> List[ProductoType]:
    productos = db.query(ProductoModel).all()
    return [
        ProductoType(
            id=p.id,
            nombre=p.nombre,
            descripcion=p.descripcion,
            precio=p.precio
        )
        for p in productos
    ]

def get_producto(db: Session, producto_id: int) -> ProductoType:
    producto = db.query(ProductoModel).filter(ProductoModel.id == producto_id).first()
    if not producto:
        raise ProductoNotFoundError(producto_id)
    return ProductoType(
        id=producto.id,
        nombre=producto.nombre,
        descripcion=producto.descripcion,
        precio=producto.precio
    )
