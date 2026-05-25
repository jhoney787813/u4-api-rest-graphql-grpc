# Arquitectura del proyecto producto-graphql

## Índice

1. [Visión general](#1-visión-general)
2. [Estructura de capas](#2-estructura-de-capas)
3. [Justificación de la arquitectura feature-oriented](#3-justificación-de-la-arquitectura-feature-oriented)
4. [Por qué FastAPI + Strawberry GraphQL](#4-por-qué-fastapi--strawberry-graphql)
5. [Integración con el servicio gRPC](#5-integración-con-el-servicio-grpc)
6. [Comparación con gRPC](#6-comparación-con-grpc)
7. [Ventajas y desventajas de GraphQL](#7-ventajas-y-desventajas-de-graphql)
8. [Cuándo usar GraphQL vs gRPC](#8-cuándo-usar-graphql-vs-grpc)
9. [Flujo de operaciones](#9-flujo-de-operaciones)

---

## 1. Visión general

```
Cliente (GraphiQL / Postman / App web)
        │
        │  POST /graphql  { query: "..." }
        ▼
┌──────────────────────────────────────────────────────┐
│                  FastAPI + Strawberry                 │
│                                                       │
│  ┌───────────────────────────────────────────────┐    │
│  │         Schema GraphQL (Query + Mutation)      │    │
│  │                                               │    │
│  │  productos     │  producto(id)                │    │
│  │  crearProducto │  actualizarProducto          │    │
│  │  eliminarProducto                             │    │
│  │  ─────────────────────────────────────────── │    │
│  │  productosGrpc (→ llama servicio gRPC)        │    │
│  │  crearProductoGrpc (→ llama servicio gRPC)    │    │
│  └───────────────────────────────────────────────┘    │
│         │                          │                  │
│         ▼                          ▼                  │
│  ┌─────────────┐          ┌──────────────────┐        │
│  │  SQLAlchemy │          │  Cliente gRPC    │        │
│  │     ORM     │          │  grpc_client/    │        │
│  └──────┬──────┘          └────────┬─────────┘        │
│         │                          │                  │
└─────────┼──────────────────────────┼──────────────────┘
          │                          │
          ▼                          ▼ HTTP/2 + Protobuf
   productos.db                localhost:50051
  (tabla productosgraphql)    (servicio gRPC →
                               tabla productosgrpc)
```

---

## 2. Estructura de capas

```
app/
├── main.py          → Presentación: schema GraphQL, registra queries/mutations, monta el router
├── database.py      → Infraestructura: engine SQLAlchemy, sesión, ruta a BD compartida
├── models/          → Dominio: modelo ORM Producto (tabla productosgraphql)
├── schemas/         → Contrato GraphQL: tipos ProductoType, ProductoInput, ProductoUpdateInput
├── resolvers/       → Lógica de negocio: queries y mutations (locales + delegadas a gRPC)
├── grpc_client/     → Cliente externo: canal gRPC, stubs, funciones de comunicación
└── core/            → Transversal: excepciones personalizadas
```

### Responsabilidades por capa

| Capa | Módulo | Responsabilidad |
|------|--------|-----------------|
| Presentación | `main.py` | Schema GraphQL, rutas, contexto de BD |
| Contrato | `schemas/` | Tipos de entrada y salida de GraphQL |
| Lógica local | `resolvers/queries.py`, `resolvers/mutations.py` | CRUD sobre `productosgraphql` |
| Lógica externa | `resolvers/grpc_resolvers.py` | Delega al cliente gRPC |
| Cliente gRPC | `grpc_client/client.py` | Canal, stub, serialización de mensajes protobuf |
| Dominio | `models/producto.py` | Mapeo ORM a la tabla `productosgraphql` |
| Infraestructura | `database.py` | Conexión a `productos.db` en la raíz compartida |
| Transversal | `core/exceptions.py` | Errores tipados reutilizables |

---

## 3. Justificación de la arquitectura feature-oriented

La organización por capas funcionales (no por tipo de archivo) tiene ventajas concretas:

- **Cohesión alta**: todo lo de `Producto` vive en módulos claramente nombrados; no hay que saltar entre carpetas genéricas para entender un flujo.
- **Bajo acoplamiento**: el resolver no conoce detalles de transporte HTTP ni del schema; solo recibe una `Session` o retorna un `ProductoType`.
- **Escalabilidad**: agregar una nueva entidad solo requiere crear sus archivos por capa sin tocar los existentes.
- **Testabilidad**: los resolvers son funciones puras que reciben dependencias inyectadas; pueden probarse sin levantar el servidor.
- **Separación clara de fuentes**: los resolvers locales y los que delegan a gRPC están en módulos distintos (`queries.py` / `grpc_resolvers.py`), lo que hace visible de dónde viene cada dato.

---

## 4. Por qué FastAPI + Strawberry GraphQL

### FastAPI

- Framework ASGI moderno con soporte nativo de `async`/`await`.
- Sistema de inyección de dependencias (`Depends`, `context_getter`) que integra limpiamente la sesión de BD en cada resolver.
- Generación automática de documentación OpenAPI para los endpoints REST complementarios.
- Ampliamente adoptado en producción; ecosistema maduro.

### Strawberry GraphQL

- Enfoque **code-first con tipado estático**: los tipos se definen con anotaciones Python estándar (`@strawberry.type`, `@strawberry.input`), sin archivos `.graphql` separados.
- Integración de primera clase con FastAPI mediante `GraphQLRouter` y `context_getter`.
- `Info[Any, None]` como tipo del parámetro `info` permite acceder al contexto (sesión de BD) de forma tipada.
- Alternativa más Pythonica que `graphene`, que requiere herencia de clases con sintaxis propia.

### SQLAlchemy 2.x + SQLite

- `DeclarativeBase` hace que los modelos sean legibles y fáciles de migrar entre motores.
- SQLite es ideal para desarrollo: sin servidor externo, el archivo se crea automáticamente.
- En producción, cambiar a PostgreSQL solo requiere modificar `DATABASE_URL` en `database.py`.

### grpcio (cliente)

- El proyecto actúa como **cliente gRPC** para comunicarse con `producto-grpc`.
- Se usa `grpc.insecure_channel` con un stub generado a partir de los mismos stubs del proyecto gRPC.
- El canal se abre y cierra por operación para evitar problemas de ciclo de vida en un entorno ASGI multihilo.

---

## 5. Integración con el servicio gRPC

### Arquitectura del cliente gRPC embebido

```
Resolver GraphQL
    │
    ▼
grpc_resolvers.py
    │  llama a
    ▼
grpc_client/client.py
    │  abre canal inseguro → localhost:50051
    │  crea stub ProductoServiceStub
    │  serializa ProductoRequest / Empty (protobuf)
    ▼
[Red: HTTP/2 + Protocol Buffers]
    │
    ▼
Servicio gRPC (producto-grpc)
    │  ejecuta CreateProducto o ListProductos
    │  escribe/lee de tabla productosgrpc
    ▼
ProductoResponse / ProductoList (protobuf)
    │
    ▼
grpc_client/client.py
    │  deserializa → ProductoType (Python)
    ▼
Schema GraphQL → respuesta JSON al cliente
```

### Nuevos campos en el schema

| Campo | Tipo GraphQL | Operación gRPC | Tabla afectada |
|-------|-------------|----------------|----------------|
| `productosGrpc` | `Query` | `ListProductos` | `productosgrpc` |
| `crearProductoGrpc` | `Mutation` | `CreateProducto` | `productosgrpc` |

### Por qué copiar los stubs en lugar de compartir el módulo

Los stubs (`producto_pb2.py`, `producto_pb2_grpc.py`) se copian al paquete `grpc_client/` en lugar de importarlos directamente desde `producto-grpc/`. Esto mantiene cada proyecto como unidad independiente y desplegable, evitando dependencias de ruta relativa entre proyectos hermanos.

El único ajuste necesario es el import en `producto_pb2_grpc.py`:
```python
# Generado originalmente (apunta al paquete del proyecto gRPC):
from app.protos import producto_pb2 as producto__pb2

# Ajustado para el contexto del proyecto GraphQL:
from app.grpc_client import producto_pb2 as producto__pb2
```

### Manejo de errores de red

Si el servidor gRPC no está disponible, el cliente captura `grpc.RpcError` y lo relanza como una excepción de Python con mensaje descriptivo. Strawberry la convierte en un error GraphQL estándar con el campo `errors` en la respuesta JSON, sin romper el servidor GraphQL.

---

## 6. Comparación con gRPC

| Aspecto | GraphQL (este proyecto) | gRPC |
|---------|------------------------|------|
| **Protocolo** | HTTP/1.1 o HTTP/2 | HTTP/2 exclusivamente |
| **Formato de datos** | JSON (texto legible) | Protocol Buffers (binario compacto) |
| **Contrato** | Schema Python con Strawberry | Archivo `.proto` externo |
| **Flexibilidad del cliente** | Alta: elige exactamente los campos | Baja: contrato fijo por RPC |
| **Rendimiento** | Moderado (JSON + overhead HTTP) | Alto (binario + multiplexación HTTP/2) |
| **Soporte en navegadores** | Nativo (HTTP + JSON) | Requiere gRPC-Web + proxy |
| **Herramientas de exploración** | GraphiQL, Apollo Studio, Postman | grpcurl, BloomRPC, Postman |
| **Debugging** | Legible en el navegador | Requiere herramientas especializadas |
| **Streaming** | Suscripciones (WebSocket) | Streaming bidireccional nativo |
| **Introspección en runtime** | Sí (schema introspectable) | No por defecto |
| **Ideal para** | APIs públicas, frontends, BFF | Microservicios internos, alto rendimiento |

---

## 7. Ventajas y desventajas de GraphQL

### Ventajas

1. **Queries flexibles**: el cliente solicita exactamente los campos necesarios, eliminando over-fetching y under-fetching.
2. **Un único endpoint**: todas las operaciones van a `/graphql`, simplificando la gestión de rutas.
3. **Schema como documentación viva**: auto-documentado e introspectable; GraphiQL lo lee en tiempo real.
4. **Evolución sin versiones**: agregar campos opcionales no rompe clientes existentes.
5. **BFF (Backend for Frontend)**: múltiples clientes (web, móvil) consumen la misma API pidiendo solo lo que necesitan.
6. **Agregación de fuentes**: un resolver puede combinar datos de la BD local y de un servicio gRPC en una sola respuesta (como hace `productosGrpc`).

### Desventajas

1. **Complejidad de caché**: GraphQL usa POST con body variable, dificultando el caché HTTP estándar.
2. **N+1 problem**: sin DataLoader, queries anidadas pueden generar múltiples consultas a la BD.
3. **Seguridad de queries**: clientes maliciosos pueden enviar queries profundamente anidadas (requiere límites de profundidad).
4. **Overhead en CRUD simple**: para operaciones básicas, REST o gRPC suelen ser más directos.
5. **Curva inicial**: el equipo debe aprender SDL, resolvers y el modelo mental de grafos.

---

## 8. Cuándo usar GraphQL vs gRPC

### Usa GraphQL cuando:

- El consumidor principal es un **frontend web o móvil** que necesita flexibilidad.
- Tienes **múltiples tipos de clientes** con necesidades de datos diferentes.
- Quieres **exploración interactiva** y documentación viva del schema.
- El proyecto tiene **datos interrelacionados** (grafos de entidades).
- Necesitas **agregar múltiples fuentes** (BD + microservicios) en una respuesta.

### Usa gRPC cuando:

- La comunicación es **entre microservicios internos** donde el rendimiento es crítico.
- Necesitas **streaming bidireccional** en tiempo real.
- El equipo trabaja en entorno **multi-lenguaje** y necesita contratos estrictos.
- El **tamaño del payload** o la **latencia** son restricciones importantes.

```
¿El cliente es un navegador o app móvil?
    Sí → GraphQL (o REST)
    No → ¿Rendimiento o streaming crítico entre servicios?
              Sí → gRPC
              No → GraphQL o REST (según complejidad del dominio)
```

---

## 9. Flujo de operaciones

### Operación local (crearProducto → tabla productosgraphql)

```
Cliente (GraphiQL / Postman)
    │  POST /graphql { mutation crearProducto(...) }
    ▼
FastAPI → GraphQLRouter
    │  context_getter inyecta sesión de BD
    ▼
Strawberry Schema → Mutation.crear_producto
    ▼
resolvers/mutations.py → crear_producto(db, data)
    │  valida nombre y precio
    │  INSERT en tabla productosgraphql
    ▼
SQLAlchemy ORM → SQLite (productos.db)
    ▼
ProductoType → JSON → cliente
```

### Operación integrada (crearProductoGrpc → tabla productosgrpc)

```
Cliente (GraphiQL / Postman)
    │  POST /graphql { mutation crearProductoGrpc(...) }
    ▼
FastAPI → GraphQLRouter
    ▼
Strawberry Schema → Mutation.crear_producto_grpc
    ▼
resolvers/grpc_resolvers.py → resolver_crear_producto_grpc(data)
    ▼
grpc_client/client.py → crear_producto_grpc(data)
    │  abre canal: grpc.insecure_channel("localhost:50051")
    │  stub.CreateProducto(ProductoRequest(...))
    │  [HTTP/2 + Protocol Buffers]
    ▼
Servicio gRPC (producto-grpc, puerto 50051)
    │  ProductoServicer.CreateProducto
    │  INSERT en tabla productosgrpc
    │  retorna ProductoResponse (protobuf)
    ▼
grpc_client/client.py
    │  deserializa → ProductoType
    ▼
JSON → cliente
```
