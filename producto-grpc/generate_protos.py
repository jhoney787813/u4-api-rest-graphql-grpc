#!/usr/bin/env python
"""
Genera los stubs de protobuf para el proyecto.

Ejecutar UNA VEZ antes de iniciar el servidor (o cada vez que
se modifique producto.proto):

    python generate_protos.py

Requiere tener instalado grpcio-tools:
    pip install grpcio-tools
"""
import subprocess
import sys
import os


def generate():
    proto_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "protos")
    proto_file = os.path.join(proto_dir, "producto.proto")

    if not os.path.exists(proto_file):
        print(f"Error: no se encontró el archivo proto en {proto_file}")
        sys.exit(1)

    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"-I{proto_dir}",
        f"--python_out={proto_dir}",
        f"--grpc_python_out={proto_dir}",
        proto_file,
    ]

    print("Generando stubs protobuf...")
    print(f"Comando: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("Error al generar stubs:")
        print(result.stderr)
        sys.exit(1)

    pb2_path = os.path.join(proto_dir, "producto_pb2.py")
    grpc_path = os.path.join(proto_dir, "producto_pb2_grpc.py")

    # protoc genera "import producto_pb2" (absoluto), pero al estar dentro
    # del paquete app.protos necesita ser un import con ruta completa.
    with open(grpc_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace(
        "import producto_pb2 as producto__pb2",
        "from app.protos import producto_pb2 as producto__pb2",
    )
    with open(grpc_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Stubs generados exitosamente:")
    print(f"  {pb2_path}")
    print(f"  {grpc_path}")
    print("\nYa puedes iniciar el servidor con:  python app/server.py")


if __name__ == "__main__":
    generate()
