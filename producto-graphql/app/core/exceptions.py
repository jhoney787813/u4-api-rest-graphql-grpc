class ProductoNotFoundError(Exception):
    def __init__(self, producto_id: int):
        self.message = f"Producto con id {producto_id} no encontrado"
        super().__init__(self.message)

class ValidationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
