# producto-graphql

API GraphQL para CRUD de Productos usando FastAPI + Strawberry + SQLAlchemy + SQLite.  
Incluye integración con el servicio gRPC (`producto-grpc`) como cliente para insertar y listar productos.

---

## Tecnologías

| Capa | Tecnología |
|------|------------|
| Framework web | FastAPI 0.115 |
| GraphQL | Strawberry-graphql 0.316 |
| ORM | SQLAlchemy 2.0 |
| Base de datos | SQLite (archivo compartido `productos.db` en la raíz) |
| Servidor ASGI | Uvicorn |
| Cliente gRPC | grpcio 1.80 + protobuf 6.x |

---

## Estructura del proyecto

```
producto-graphql/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Schema GraphQL completo, router FastAPI
│   ├── database.py              # Engine, SessionLocal, Base, get_db
│   ├── models/
│   │   └── producto.py          # Modelo ORM → tabla productosgraphql
│   ├── schemas/
│   │   └── producto_schema.py   # Tipos Strawberry: ProductoType, ProductoInput, ProductoUpdateInput
│   ├── resolvers/
│   │   ├── queries.py           # Queries locales: get_productos, get_producto
│   │   ├── mutations.py         # Mutations locales: crear, actualizar, eliminar
│   │   └── grpc_resolvers.py    # Resolvers que delegan al servicio gRPC
│   ├── grpc_client/
│   │   ├── __init__.py
│   │   ├── producto_pb2.py      # Stubs protobuf (copiados del proyecto gRPC)
│   │   ├── producto_pb2_grpc.py # Stubs gRPC (con import ajustado)
│   │   └── client.py            # Canal gRPC + funciones crear/listar vía gRPC
│   └── core/
│       └── exceptions.py        # ProductoNotFoundError, ValidationError
├── requirements.txt
├── .gitignore
├── README.md
└── ARQUITECTURA.md
```

---

## Base de datos compartida

La base de datos `productos.db` se ubica en la raíz del repositorio (`u4-api-rest-graphql-grpc/`), compartida entre ambos proyectos. Cada proyecto escribe en su propia tabla:

| Proyecto | Tabla |
|----------|-------|
| producto-graphql | `productosgraphql` |
| producto-grpc | `productosgrpc` |

---

## Instalación

```bash
# Desde el directorio producto-graphql/
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

---

## Ejecución

```bash
uvicorn app.main:app --reload
```

El servidor arranca en `http://127.0.0.1:8000`.

| Endpoint | Descripción |
|----------|-------------|
| `GET /` | Mensaje de bienvenida |
| `GET /graphql` | GraphiQL (interfaz interactiva en el navegador) |
| `POST /graphql` | Endpoint GraphQL para queries y mutations |

---

## Campos GraphQL disponibles

### Queries

| Campo | Descripción | Fuente de datos |
|-------|-------------|-----------------|
| `productos` | Lista todos los productos locales | Tabla `productosgraphql` |
| `producto(id)` | Obtiene un producto por ID | Tabla `productosgraphql` |
| `productosGrpc` | Lista productos llamando al servicio gRPC | Tabla `productosgrpc` via gRPC |

### Mutations

| Campo | Descripción | Destino |
|-------|-------------|---------|
| `crearProducto` | Crea un producto localmente | Tabla `productosgraphql` |
| `actualizarProducto` | Actualiza un producto local | Tabla `productosgraphql` |
| `eliminarProducto` | Elimina un producto local | Tabla `productosgraphql` |
| `crearProductoGrpc` | Crea un producto llamando al servicio gRPC | Tabla `productosgrpc` via gRPC |

---

## Ejemplos — Operaciones locales (tabla productosgraphql)

### Listar todos los productos

```graphql
query {
  productos {
    id
    nombre
    descripcion
    precio
  }
}
```

**Respuesta:**
```json
{
  "data": {
    "productos": [
      { "id": 1, "nombre": "Laptop Gamer", "descripcion": "Intel i7, 16GB RAM", "precio": 1299.99 }
    ]
  }
}
```

---

### Obtener un producto por ID

```graphql
query {
  producto(id: 1) {
    id
    nombre
    descripcion
    precio
  }
}
```

**Si no existe:**
```json
{
  "data": { "producto": null },
  "errors": [{ "message": "Producto con id 99 no encontrado" }]
}
```

---

### Crear un producto

```graphql
mutation {
  crearProducto(data: {
    nombre: "Laptop Gamer"
    descripcion: "Intel i7, 16GB RAM"
    precio: 1299.99
  }) {
    id
    nombre
    precio
  }
}
```

**Sin descripción (campo opcional):**
```graphql
mutation {
  crearProducto(data: {
    nombre: "Mouse Inalámbrico"
    precio: 29.99
  }) {
    id
    nombre
    descripcion
    precio
  }
}
```

---

### Actualizar un producto

```graphql
mutation {
  actualizarProducto(id: 1, data: {
    precio: 999.99
  }) {
    id
    nombre
    precio
  }
}
```

```graphql
mutation {
  actualizarProducto(id: 1, data: {
    nombre: "Laptop Gamer Pro"
    descripcion: "Intel i9, 32GB RAM, RTX 4080"
  }) {
    id
    nombre
    descripcion
    precio
  }
}
```

---

### Eliminar un producto

```graphql
mutation {
  eliminarProducto(id: 1)
}
```

---

## Ejemplos — Integración con el servicio gRPC

> **Requisito previo:** el servidor gRPC debe estar corriendo en `localhost:50051`.
>
> ```bash
> # En otra terminal, desde producto-grpc/
> venv\Scripts\activate
> python app/server.py
> ```

---

### Insertar un producto via gRPC (escribe en tabla productosgrpc)

```graphql
mutation {
  crearProductoGrpc(data: {
    nombre: "Monitor 4K"
    descripcion: "LG 27 pulgadas IPS"
    precio: 450.00
  }) {
    id
    nombre
    descripcion
    precio
  }
}
```

**Respuesta:**
```json
{
  "data": {
    "crearProductoGrpc": {
      "id": 1,
      "nombre": "Monitor 4K",
      "descripcion": "LG 27 pulgadas IPS",
      "precio": 450.0
    }
  }
}
```

**Si el servidor gRPC no está disponible:**
```json
{
  "errors": [{ "message": "Error gRPC [StatusCode.UNAVAILABLE]: ..." }]
}
```

---

### Listar productos del servicio gRPC (lee de tabla productosgrpc)

```graphql
query {
  productosGrpc {
    id
    nombre
    descripcion
    precio
  }
}
```

**Respuesta:**
```json
{
  "data": {
    "productosGrpc": [
      { "id": 1, "nombre": "Monitor 4K", "descripcion": "LG 27 pulgadas IPS", "precio": 450.0 }
    ]
  }
}
```

---

## Uso con Postman

**URL:** `POST http://127.0.0.1:8000/graphql`  
**Header:** `Content-Type: application/json`

**Body — crear producto local:**
```json
{
  "query": "mutation { crearProducto(data: { nombre: \"Teclado Mecánico\", descripcion: \"Switch Blue RGB\", precio: 89.99 }) { id nombre precio } }"
}
```

**Body — crear via gRPC:**
```json
{
  "query": "mutation { crearProductoGrpc(data: { nombre: \"Auriculares Sony\", descripcion: \"WH-1000XM5\", precio: 279.99 }) { id nombre precio } }"
}
```

**Body — listar via gRPC:**
```json
{
  "query": "query { productosGrpc { id nombre descripcion precio } }"
}
```

**Con variables GraphQL:**
```json
{
  "query": "mutation CrearGrpc($data: ProductoInput!) { crearProductoGrpc(data: $data) { id nombre precio } }",
  "variables": {
    "data": {
      "nombre": "Auriculares Sony",
      "descripcion": "WH-1000XM5",
      "precio": 279.99
    }
  }
}
```

---

## Cómo ejecutar ambos proyectos simultáneamente

```
Terminal 1 (GraphQL):           Terminal 2 (gRPC):
─────────────────────           ──────────────────
cd producto-graphql             cd producto-grpc
venv\Scripts\activate           venv\Scripts\activate
uvicorn app.main:app --reload   python app/server.py
```

Con ambos corriendo:
- Operaciones locales GraphQL → `http://localhost:8000/graphql`
- Operaciones via gRPC desde GraphQL → misma URL, usa campos `*Grpc`

---

## Validaciones

| Campo | Regla |
|-------|-------|
| `nombre` | Obligatorio, no vacío ni solo espacios |
| `descripcion` | Opcional, puede ser `null` |
| `precio` | Obligatorio, debe ser >= 0 |

Las mismas validaciones aplican tanto en operaciones locales como en las que delegan al gRPC  
(la validación ocurre en el servicer gRPC, que retorna `INVALID_ARGUMENT` con el mensaje de error).

---

## Notas

- `productos.db` se crea automáticamente en la raíz al arrancar el servidor.
- El archivo `productos.db` está excluido del repositorio via `.gitignore`.
- Para reiniciar los datos, elimina `productos.db` en la raíz del proyecto.
- Los stubs en `app/grpc_client/` son copias de los generados en `producto-grpc/`; si se modifica el `.proto` en ese proyecto, se deben actualizar manualmente.
