"""
Cliente de prueba para el servicio gRPC de Productos.

Prueba los 5 métodos CRUD más casos de error.

Requisitos previos:
    1. python generate_protos.py
    2. python app/server.py   (en otra terminal)

Luego ejecutar:
    python client_test.py
"""
import grpc
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.protos import producto_pb2, producto_pb2_grpc


def separador(titulo: str = "") -> None:
    linea = "=" * 60
    if titulo:
        print(f"\n{linea}")
        print(f"  {titulo}")
        print(linea)
    else:
        print(linea)


def run_tests() -> None:
    channel = grpc.insecure_channel("localhost:50051")
    stub = producto_pb2_grpc.ProductoServiceStub(channel)

    separador("PRUEBAS DEL SERVICIO gRPC — ProductoService")

    # ------------------------------------------------------------------
    # 1. CREATE
    # ------------------------------------------------------------------
    print("\n[1] CREATE — Crear productos de ejemplo")
    productos_data = [
        {
            "nombre": "Laptop Gamer",
            "descripcion": "Intel i7, 16 GB RAM, RTX 4070",
            "precio": 1299.99,
        },
        {
            "nombre": "Mouse Inalámbrico",
            "descripcion": "Logitech MX Master 3",
            "precio": 89.99,
        },
        {
            "nombre": "Teclado Mecánico",
            "descripcion": "Cherry MX Red switches",
            "precio": 149.99,
        },
    ]

    ids_creados: list[int] = []
    for data in productos_data:
        req = producto_pb2.ProductoRequest(
            nombre=data["nombre"],
            descripcion=data["descripcion"],
            precio=data["precio"],
        )
        resp = stub.CreateProducto(req)
        print(f"   Creado  → ID={resp.id} | {resp.nombre} | ${resp.precio:.2f}")
        ids_creados.append(resp.id)

    # ------------------------------------------------------------------
    # 2. LIST
    # ------------------------------------------------------------------
    print("\n[2] LIST — Listar todos los productos")
    resp = stub.ListProductos(producto_pb2.Empty())
    print(f"   Total en BD: {len(resp.productos)}")
    for p in resp.productos:
        print(f"   [{p.id}] {p.nombre:25s} ${p.precio:>9.2f}  |  {p.descripcion}")

    # ------------------------------------------------------------------
    # 3. GET
    # ------------------------------------------------------------------
    print("\n[3] GET — Obtener producto por ID")
    if ids_creados:
        resp = stub.GetProducto(producto_pb2.ProductoId(id=ids_creados[0]))
        print(f"   Obtenido → ID={resp.id} | {resp.nombre} | ${resp.precio:.2f}")

    # ------------------------------------------------------------------
    # 4. UPDATE
    # ------------------------------------------------------------------
    print("\n[4] UPDATE — Actualizar precio del primer producto")
    if ids_creados:
        req = producto_pb2.UpdateProductoRequest(
            id=ids_creados[0],
            precio=999.99,
            update_precio=True,
        )
        resp = stub.UpdateProducto(req)
        print(
            f"   Actualizado → ID={resp.id} | {resp.nombre} | "
            f"Nuevo precio: ${resp.precio:.2f}"
        )

    # UPDATE nombre + descripcion
    print("\n[4b] UPDATE — Actualizar nombre y descripción del segundo producto")
    if len(ids_creados) >= 2:
        req = producto_pb2.UpdateProductoRequest(
            id=ids_creados[1],
            nombre="Mouse Logitech Pro",
            descripcion="Edición especial gaming",
            update_nombre=True,
            update_descripcion=True,
        )
        resp = stub.UpdateProducto(req)
        print(
            f"   Actualizado → ID={resp.id} | {resp.nombre} | {resp.descripcion}"
        )

    # ------------------------------------------------------------------
    # 5. DELETE
    # ------------------------------------------------------------------
    # # print("\n[5] DELETE — Eliminar el último producto creado")
    # # if ids_creados:
    # #     resp = stub.DeleteProducto(producto_pb2.ProductoId(id=ids_creados[-1]))
    # #     print(f"   Resultado → success={resp.success} | {resp.message}")

    # ------------------------------------------------------------------
    # 6. ERROR: GET producto inexistente
    # ------------------------------------------------------------------
    print("\n[6] ERROR — GET producto inexistente (ID=9999)")
    try:
        resp = stub.GetProducto(producto_pb2.ProductoId(id=9999))
        print(f"   Resultado inesperado: {resp}")
    except grpc.RpcError as e:
        print(f"   Error esperado: code={e.code()} | {e.details()}")

    # ------------------------------------------------------------------
    # 7. ERROR: precio negativo
    # ------------------------------------------------------------------
    print("\n[7] ERROR — Crear producto con precio negativo")
    try:
        req = producto_pb2.ProductoRequest(nombre="Producto Inválido", precio=-50.0)
        resp = stub.CreateProducto(req)
        print(f"   Resultado inesperado: {resp}")
    except grpc.RpcError as e:
        print(f"   Error esperado: code={e.code()} | {e.details()}")

    # ------------------------------------------------------------------
    # 8. ERROR: nombre vacío
    # ------------------------------------------------------------------
    print("\n[8] ERROR — Crear producto con nombre vacío")
    try:
        req = producto_pb2.ProductoRequest(nombre="   ", precio=10.0)
        resp = stub.CreateProducto(req)
        print(f"   Resultado inesperado: {resp}")
    except grpc.RpcError as e:
        print(f"   Error esperado: code={e.code()} | {e.details()}")

    # ------------------------------------------------------------------
    # 9. LIST PRODUCTOS GraphQL (llama al API GraphQL desde gRPC)
    # ------------------------------------------------------------------
    print("\n[9] LIST GRAPHQL — Listar productos vía API GraphQL (tabla productosgraphql)")
    try:
        resp = stub.ListProductosGraphQL(producto_pb2.Empty())
        print(f"   Total desde GraphQL: {len(resp.productos)}")
        for p in resp.productos:
            print(f"   [{p.id}] {p.nombre:25s} ${p.precio:>9.2f}  |  {p.descripcion}")
        if not resp.productos:
            print("   (sin datos — inserta productos desde el API GraphQL primero)")
    except grpc.RpcError as e:
        print(f"   Error: code={e.code()} | {e.details()}")
        print("   (verifica que el servidor GraphQL esté corriendo en localhost:8000)")

    separador("PRUEBAS COMPLETADAS")
    channel.close()


if __name__ == "__main__":
    run_tests()
