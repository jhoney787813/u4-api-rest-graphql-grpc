from sqlalchemy import Column, Integer, String, Float
from app.database import Base

class Producto(Base):
    __tablename__ = "productosgrpc"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    precio = Column(Float, nullable=False)
