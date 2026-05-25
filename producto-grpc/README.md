# producto-grpc

Servicio gRPC para CRUD de Productos con **grpcio**, **SQLAlchemy 2** y **SQLite**.  
Incluye integración con el API GraphQL (`producto-graphql`) como cliente HTTP para listar productos.

---

## Tecnologías

| Capa | Tecnología |
|------|------------|
| Protocolo | gRPC (HTTP/2 + Protocol Buffers) |
| Framework gRPC | grpcio 1.80 |
| Compilador de protos | grpcio-tools 1.80 |
| ORM | SQLAlchemy 2.0 |
| Base de datos | SQLite (archivo compartido `productos.db` en la raíz) |
| Serialización | protobuf 6.x |
| Cliente GraphQL | urllib (stdlib Python, sin dependencias extra) |

---

## Estructura del proyecto

```
producto-grpc/
├── app/
│   ├── __init__.py
│   ├── database.py              # Engine SQLAlchemy, SessionLocal, Base
│   ├── server.py                # Bootstrap del servidor gRPC en :50051
│   ├── core/
│   │   └── exceptions.py        # GrpcError + helpers NOT_FOUND / INVALID_ARGUMENT / INTERNAL
│   ├── models/
│   │   └── producto.py          # Modelo ORM → tabla productosgrpc
│   ├── protos/
│   │   ├── producto.proto        # Contrato gRPC (6 RPCs)
│   │   ├── producto_pb2.py       # Generado por protoc
│   │   └── producto_pb2_grpc.py  # Generado por protoc (import parchado)
│   ├── services/
│   │   └── producto_service.py   # ProductoServicer: implementación de todos los RPCs
│   └── graphql_client/
│       ├── __init__.py
│       └── client.py             # Cliente HTTP que llama al API GraphQL
├── client_test.py                # Cliente de prueba (CRUD + integración GraphQL)
├── generate_protos.py            # Genera y parchea los stubs protobuf
├── requirements.txt
├── .gitignore
├── README.md
└── ARQUITECTURA.md
```

---

## Base de datos compartida

La base de datos `productos.db` se ubica en la raíz del repositorio, compartida con el proyecto GraphQL:

| Proyecto | Tabla |
|----------|-------|
| producto-grpc | `productosgrpc` |
| producto-graphql | `productosgraphql` |

---

## Instalación y ejecución

### 1. Crear y activar entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Generar los stubs protobuf

**Obligatorio** antes del primer arranque y después de modificar `producto.proto`:

```bash
python generate_protos.py
```

Salida esperada:
```
Generando stubs protobuf...
Stubs generados exitosamente:
  .../app/protos/producto_pb2.py
  .../app/protos/producto_pb2_grpc.py

Ya puedes iniciar el servidor con:  python app/server.py
```

### 4. Iniciar el servidor gRPC

```bash
python app/server.py
```

Salida esperada:
```
Servidor gRPC corriendo en [::]:50051
Presiona Ctrl+C para detener
```

### 5. Ejecutar el cliente de prueba

En **otra terminal** (con el venv activo):

```bash
python client_test.py
```

El script ejecuta 9 pruebas: 5 CRUD + 3 casos de error + 1 integración con GraphQL.

---

## Métodos RPC disponibles

### Operaciones locales (tabla productosgrpc)

#### `CreateProducto`

Crea un nuevo producto en la tabla `productosgrpc`.

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `nombre` | string | Sí | No vacío |
| `descripcion` | string | No | Opcional |
| `precio` | double | Sí | >= 0 |

Retorna `ProductoResponse` con el producto creado (incluye `id` autoincremental).

---

#### `ListProductos`

Lista todos los productos de la tabla `productosgrpc`.

- Entrada: `Empty`
- Salida: `ProductoList { productos: [ProductoResponse] }`

---

#### `GetProducto`

Busca un producto por ID en la tabla `productosgrpc`.

- Entrada: `ProductoId { id: int32 }`
- Salida: `ProductoResponse`
- Error `NOT_FOUND` si el ID no existe

---

#### `UpdateProducto`

Actualización parcial. Solo modifica los campos cuya bandera `update_*` sea `true`.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | int32 | ID del producto |
| `nombre` + `update_nombre` | string + bool | Actualiza el nombre si la bandera es true |
| `descripcion` + `update_descripcion` | string + bool | Actualiza la descripción si la bandera es true |
| `precio` + `update_precio` | double + bool | Actualiza el precio si la bandera es true |

---

#### `DeleteProducto`

Elimina un producto de la tabla `productosgrpc`.

- Entrada: `ProductoId { id: int32 }`
- Salida: `DeleteResponse { success: bool, message: string }`

---

### Integración con el API GraphQL

#### `ListProductosGraphQL`

Llama al API GraphQL (`http://localhost:8000/graphql`) y retorna los productos de la tabla `productosgraphql`.

- Entrada: `Empty`
- Salida: `ProductoList { productos: [ProductoResponse] }`
- Requiere que el servidor GraphQL esté corriendo en `localhost:8000`
- Error `INTERNAL` si el servidor GraphQL no está disponible

---

## Pruebas con client_test.py

El script prueba los 9 escenarios en orden:

| # | Prueba | Descripción |
|---|--------|-------------|
| 1 | CREATE | Crea 3 productos en `productosgrpc` |
| 2 | LIST | Lista todos en `productosgrpc` |
| 3 | GET | Obtiene el primero por ID |
| 4 | UPDATE precio | Actualiza solo el precio |
| 4b | UPDATE nombre+desc | Actualiza nombre y descripción |
| 6 | ERROR NOT_FOUND | GET con ID=9999 → espera error |
| 7 | ERROR precio negativo | CREATE con precio=-50 → espera error |
| 8 | ERROR nombre vacío | CREATE con nombre="   " → espera error |
| **9** | **LIST GraphQL** | **Llama al API GraphQL y lista `productosgraphql`** |

Para que la prueba `[9]` tenga datos, primero inserta productos en el API GraphQL:

```bash
# En el API GraphQL (http://localhost:8000/graphql):
mutation {
  crearProducto(data: { nombre: "Producto desde GraphQL", precio: 99.99 }) {
    id nombre
  }
}
```

---

## Pruebas con grpcurl

```bash
# Instalar (Windows con Chocolatey)
choco install grpcurl

# Listar servicios
grpcurl -plaintext -import-path ./app/protos -proto producto.proto list

# Listar métodos
grpcurl -plaintext -import-path ./app/protos -proto producto.proto list producto.ProductoService
```

### CreateProducto

```bash
grpcurl -plaintext \
  -import-path ./app/protos -proto producto.proto \
  -d '{"nombre": "Auriculares Sony", "descripcion": "WH-1000XM5", "precio": 279.99}' \
  localhost:50051 producto.ProductoService/CreateProducto
```

### ListProductos

```bash
grpcurl -plaintext \
  -import-path ./app/protos -proto producto.proto \
  -d '{}' \
  localhost:50051 producto.ProductoService/ListProductos
```

### GetProducto

```bash
grpcurl -plaintext \
  -import-path ./app/protos -proto producto.proto \
  -d '{"id": 1}' \
  localhost:50051 producto.ProductoService/GetProducto
```

### UpdateProducto (solo precio)

```bash
grpcurl -plaintext \
  -import-path ./app/protos -proto producto.proto \
  -d '{"id": 1, "precio": 249.99, "update_precio": true}' \
  localhost:50051 producto.ProductoService/UpdateProducto
```

### DeleteProducto

```bash
grpcurl -plaintext \
  -import-path ./app/protos -proto producto.proto \
  -d '{"id": 1}' \
  localhost:50051 producto.ProductoService/DeleteProducto
```

### ListProductosGraphQL (requiere servidor GraphQL en :8000)

```bash
grpcurl -plaintext \
  -import-path ./app/protos -proto producto.proto \
  -d '{}' \
  localhost:50051 producto.ProductoService/ListProductosGraphQL
```

---

## Pruebas con Postman

1. **New > gRPC Request** → URL: `localhost:50051`
2. Importar `app/protos/producto.proto`
3. Seleccionar el método y completar el payload JSON

---

## Cómo ejecutar ambos proyectos simultáneamente

```
Terminal 1 (gRPC):              Terminal 2 (GraphQL):
──────────────────              ─────────────────────
cd producto-grpc                cd producto-graphql
venv\Scripts\activate           venv\Scripts\activate
python app/server.py            uvicorn app.main:app --reload

Terminal 3 (pruebas):
─────────────────────
cd producto-grpc
venv\Scripts\activate
python client_test.py
```

---

## Códigos de error gRPC

| Código | Nombre | Cuándo se produce |
|--------|--------|-------------------|
| 5 | `NOT_FOUND` | Producto no encontrado por ID |
| 3 | `INVALID_ARGUMENT` | Nombre vacío o precio negativo |
| 13 | `INTERNAL` | Error inesperado en BD o al contactar el API GraphQL |

---

## Regenerar stubs tras cambios en el proto

```bash
# 1. Edita app/protos/producto.proto
# 2. Regenera (también parchea el import automáticamente)
python generate_protos.py
# 3. Reinicia el servidor
python app/server.py
```
