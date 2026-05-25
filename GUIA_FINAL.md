# Guía Final — Proyectos GraphQL y gRPC

---

## 1. Comandos para arrancar desde cero

### PROYECTO 1 — GraphQL (FastAPI + Strawberry)

```bash
cd producto-graphql

# Crear entorno virtual
python -m venv venv

# Activar (Windows)
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor (crea productos.db automáticamente)
uvicorn app.main:app --reload

# Acceder a GraphiQL en el navegador:
# http://127.0.0.1:8000/graphql
```

### PROYECTO 2 — gRPC (grpcio + SQLAlchemy)

```bash
cd producto-grpc

# Crear entorno virtual
python -m venv venv

# Activar (Windows)
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# PASO OBLIGATORIO: generar stubs protobuf
python generate_protos.py

# Iniciar servidor gRPC (crea productos.db automáticamente)
python app/server.py

# En OTRA terminal (con el venv activado), correr cliente de prueba:
python client_test.py
```

---

## 2. Queries y Mutations GraphQL — Listos para GraphiQL / Postman

### URL: `http://127.0.0.1:8000/graphql`
### Postman: POST a `http://127.0.0.1:8000/graphql` con body `{"query": "..."}` (Content-Type: application/json)

---

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

---

### Obtener producto por ID

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

---

### Crear un producto

```graphql
mutation {
  crearProducto(data: {
    nombre: "Laptop Gamer"
    descripcion: "Intel i7, 16GB RAM, RTX 4070"
    precio: 1299.99
  }) {
    id
    nombre
    descripcion
    precio
  }
}
```

### Crear producto sin descripción (campo opcional)

```graphql
mutation {
  crearProducto(data: {
    nombre: "Cable USB-C"
    precio: 12.50
  }) {
    id
    nombre
    precio
  }
}
```

---

### Actualizar producto (solo precio)

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

### Actualizar producto (nombre + descripción)

```graphql
mutation {
  actualizarProducto(id: 1, data: {
    nombre: "Laptop Pro"
    descripcion: "Intel i9, 32GB RAM, RTX 4090"
  }) {
    id
    nombre
    descripcion
    precio
  }
}
```

---

### Eliminar producto

```graphql
mutation {
  eliminarProducto(id: 2)
}
```

---

### Postman — Body JSON para crear producto

```json
{
  "query": "mutation { crearProducto(data: { nombre: \"Monitor 4K\", descripcion: \"LG 27 pulgadas\", precio: 450.00 }) { id nombre precio } }"
}
```

---

## 3. Pruebas gRPC — client_test.py

```bash
# Terminal 1: servidor corriendo
python app/server.py

# Terminal 2: ejecutar todas las pruebas
python client_test.py
```

El cliente prueba automáticamente:
1. **CREATE** — crea 3 productos
2. **LIST** — lista todos los productos
3. **GET** — obtiene el producto con ID del primero creado
4. **UPDATE** — actualiza el precio del primer producto
5. **DELETE** — elimina el último producto creado
6. **ERROR: NOT_FOUND** — intenta obtener ID=9999 (esperado: error gRPC)
7. **ERROR: INVALID_ARGUMENT** — intenta crear con precio negativo (esperado: error gRPC)

### Probar con grpcurl (opcional)

```bash
# Instalar grpcurl: https://github.com/fullstorydev/grpcurl

# Listar servicios disponibles
grpcurl -plaintext localhost:50051 list

# Listar todos los productos
grpcurl -plaintext -d '{}' localhost:50051 producto.ProductoService/ListProductos

# Crear producto
grpcurl -plaintext -d '{
  "nombre": "Teclado Mecánico",
  "descripcion": "Cherry MX Red",
  "precio": 149.99
}' localhost:50051 producto.ProductoService/CreateProducto

# Obtener por ID
grpcurl -plaintext -d '{"id": 1}' localhost:50051 producto.ProductoService/GetProducto

# Actualizar precio
grpcurl -plaintext -d '{
  "id": 1,
  "precio": 129.99,
  "update_precio": true
}' localhost:50051 producto.ProductoService/UpdateProducto

# Eliminar
grpcurl -plaintext -d '{"id": 1}' localhost:50051 producto.ProductoService/DeleteProducto
```

---

## 4. Sugerencias para el video de máximo 15 minutos

### Estructura sugerida (15 min)

| Tiempo | Sección |
|--------|---------|
| 0:00 – 1:30 | Introducción: qué son GraphQL y gRPC, diferencias clave |
| 1:30 – 2:30 | Mostrar estructura de carpetas de ambos proyectos (feature-oriented) |
| 2:30 – 5:30 | **Demo GraphQL**: arrancar servidor, abrir GraphiQL, ejecutar las 5 operaciones CRUD en vivo |
| 5:30 – 8:00 | Mostrar código relevante GraphQL: schema Strawberry, resolver, modelo ORM |
| 8:00 – 10:30 | **Demo gRPC**: mostrar el .proto, generar stubs, arrancar servidor, ejecutar client_test.py |
| 10:30 – 12:30 | Mostrar código relevante gRPC: ProductoServicer, manejo de errores con StatusCode |
| 12:30 – 14:00 | Comparación directa: cuándo usar GraphQL vs gRPC |
| 14:00 – 15:00 | Conclusiones y cierre |

---

### Lo más impactante para mostrar

**GraphQL:**
- Abrir `http://localhost:8000/graphql` en el navegador → GraphiQL se ve profesional
- Mostrar que una sola query puede pedir solo los campos necesarios (selección de campos)
- Mostrar errores tipados cuando se pasa ID inexistente o precio negativo

**gRPC:**
- Mostrar el `.proto` como "contrato" entre cliente y servidor
- Ejecutar `python generate_protos.py` y ver cómo se generan los stubs automáticamente
- Ejecutar `client_test.py` y ver los 7 tests pasar en consola
- Mostrar el manejo de errores con `grpc.StatusCode.NOT_FOUND`

**Comparación:**
- GraphQL: flexible, ideal para APIs públicas y frontends
- gRPC: rápido, tipado, ideal para microservicios internos
- Ambos usan el mismo ORM (SQLAlchemy) y la misma base de datos (SQLite)

---

## 5. Resumen de endpoints/puertos

| Proyecto | Puerto | URL/Comando |
|----------|--------|-------------|
| GraphQL  | 8000   | `http://localhost:8000/graphql` |
| gRPC     | 50051  | `grpcurl localhost:50051` o `python client_test.py` |
