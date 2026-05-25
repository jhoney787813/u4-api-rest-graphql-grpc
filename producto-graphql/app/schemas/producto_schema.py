import strawberry
from typing import Optional, List

@strawberry.type
class ProductoType:
    id: int
    nombre: str
    descripcion: Optional[str]
    precio: float

@strawberry.input
class ProductoInput:
    nombre: str
    descripcion: Optional[str] = None
    precio: float

@strawberry.input
class ProductoUpdateInput:
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
