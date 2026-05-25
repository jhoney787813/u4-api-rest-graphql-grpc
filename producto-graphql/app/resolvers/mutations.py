from sqlalchemy.orm import Session
from app.models.producto import Producto as ProductoModel
from app.schemas.producto_schema import ProductoType, ProductoInput, ProductoUpdateInput
from app.core.exceptions import ProductoNotFoundError, ValidationError

def crear_producto(db: Session, data: ProductoInput) -> ProductoType:
    if not data.nombre or not data.nombre.strip():
        raise ValidationError("El nombre no puede estar vacío")
    if data.precio < 0:
        raise ValidationError("El precio debe ser mayor o igual a 0")

    producto = ProductoModel(
        nombre=data.nombre.strip(),
        descripcion=data.descripcion,
        precio=data.precio
    )
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return ProductoType(
        id=producto.id,
        nombre=producto.nombre,
        descripcion=producto.descripcion,
        precio=producto.precio
    )

def actualizar_producto(db: Session, producto_id: int, data: ProductoUpdateInput) -> ProductoType:
    producto = db.query(ProductoModel).filter(ProductoModel.id == producto_id).first()
    if not producto:
        raise ProductoNotFoundError(producto_id)

    if data.nombre is not None:
        if not data.nombre.strip():
            raise ValidationError("El nombre no puede estar vacío")
        producto.nombre = data.nombre.strip()
    if data.descripcion is not None:
        producto.descripcion = data.descripcion
    if data.precio is not None:
        if data.precio < 0:
            raise ValidationError("El precio debe ser mayor o igual a 0")
        producto.precio = data.precio

    db.commit()
    db.refresh(producto)
    return ProductoType(
        id=producto.id,
        nombre=producto.nombre,
        descripcion=producto.descripcion,
        precio=producto.precio
    )

def eliminar_producto(db: Session, producto_id: int) -> bool:
    producto = db.query(ProductoModel).filter(ProductoModel.id == producto_id).first()
    if not producto:
        raise ProductoNotFoundError(producto_id)
    db.delete(producto)
    db.commit()
    return True
