"""
Punto de entrada del servidor gRPC.

Uso:
    python app/server.py

Antes de correr por primera vez, asegúrate de haber generado los stubs:
    python generate_protos.py
"""
import grpc
import sys
import os
from concurrent import futures

# Garantiza que el paquete raíz esté en el path cuando se ejecuta directamente
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app.protos import producto_pb2_grpc
from app.services.producto_service import ProductoServicer

_HOST = "[::]:50051"
_MAX_WORKERS = 10


def serve() -> None:
    # Crea las tablas si no existen
    Base.metadata.create_all(bind=engine)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS))
    producto_pb2_grpc.add_ProductoServiceServicer_to_server(ProductoServicer(), server)

    server.add_insecure_port(_HOST)
    server.start()

    print(f"Servidor gRPC corriendo en {_HOST}")
    print("Presiona Ctrl+C para detener\n")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nApagando servidor...")
        server.stop(grace=5)
        print("Servidor detenido.")


if __name__ == "__main__":
    serve()
