import grpc

class GrpcError(Exception):
    def __init__(self, code: grpc.StatusCode, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

def handle_grpc_error(context, error: GrpcError):
    context.set_code(error.code)
    context.set_details(error.message)

def not_found_error(producto_id: int) -> GrpcError:
    return GrpcError(
        grpc.StatusCode.NOT_FOUND,
        f"Producto con id {producto_id} no encontrado"
    )

def invalid_argument_error(message: str) -> GrpcError:
    return GrpcError(grpc.StatusCode.INVALID_ARGUMENT, message)

def internal_error(message: str) -> GrpcError:
    return GrpcError(grpc.StatusCode.INTERNAL, message)
