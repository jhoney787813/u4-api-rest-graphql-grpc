# Arquitectura del proyecto producto-grpc

## Índice

1. [Visión general](#1-visión-general)
2. [Estructura de capas](#2-estructura-de-capas)
3. [Justificación de la arquitectura](#3-justificación-de-la-arquitectura)
4. [Por qué gRPC + protobuf + grpcio](#4-por-qué-grpc--protobuf--grpcio)
5. [Integración con el API GraphQL](#5-integración-con-el-api-graphql)
6. [Decisiones de diseño clave](#6-decisiones-de-diseño-clave)
7. [Flujo de operaciones](#7-flujo-de-operaciones)
8. [Comparación gRPC vs GraphQL](#8-comparación-grpc-vs-graphql)
9. [Cuándo usar gRPC vs GraphQL](#9-cuándo-usar-grpc-vs-graphql)
10. [Ventajas y desventajas de gRPC](#10-ventajas-y-desventajas-de-grpc)

---

## 1. Visión general

```
Cliente (Python / grpcurl / Postman)
        │
        │  HTTP/2  +  Protocol Buffers (binario)
        ▼
┌─────────────────────────────────────────────────────────┐
│                   Servidor gRPC :50051                   │
│              grpc.server (ThreadPoolExecutor)            │
│                                                          │
│  ┌───────────────────────────────────────────────────┐   │
│  │              ProductoServicer                      │   │
│  │          (app/services/producto_service)           │   │
│  │                                                    │   │
│  │  CreateProducto   │  ListProductos                 │   │
│  │  GetProducto      │  UpdateProducto                │   │
│  │  DeleteProducto                                    │   │
│  │  ──────────────────────────────────────────────── │   │
│  │  ListProductosGraphQL (→ llama API GraphQL HTTP)   │   │
│  └───────────────┬──────────────────────┬─────────────┘   │
│                  │                      │                  │
│         ┌────────▼──────┐    ┌──────────▼──────────┐      │
│         │ SQLAlchemy ORM│    │  Cliente GraphQL     │      │
│         │ SessionLocal  │    │  graphql_client/     │      │
│         └────────┬──────┘    └──────────┬──────────-┘      │
│                  │                      │                  │
└──────────────────┼──────────────────────┼──────────────────┘
                   │                      │
                   ▼                      ▼ HTTP/1.1 + JSON
             productos.db            localhost:8000
          (tabla productosgrpc)    (API GraphQL →
                                    tabla productosgraphql)
```

---

## 2. Estructura de capas

```
app/
├── server.py         → Bootstrap: arranca gRPC, registra el servicer
├── database.py       → Infraestructura: engine, SessionLocal, ruta a BD compartida
├── models/           → Dominio: Producto ORM (tabla productosgrpc)
├── protos/           → Contrato: producto.proto + stubs generados
├── core/exceptions   → Transversal: GrpcError, códigos StatusCode
├── services/         → Aplicación: ProductoServicer — todos los handlers RPC
└── graphql_client/   → Cliente externo: HTTP hacia el API GraphQL
```

### Responsabilidades por capa

| Capa | Módulo | Responsabilidad |
|------|--------|-----------------|
| Bootstrap | `server.py` | Crear el servidor gRPC, registrar el servicer, esperar conexiones |
| Contrato | `protos/producto.proto` | Fuente de verdad de la API; define mensajes y RPCs |
| Generado | `protos/producto_pb2*.py` | Stubs tipados para serializar/deserializar mensajes |
| Lógica local | `services/producto_service.py` | CRUD sobre `productosgrpc` + integración GraphQL |
| Cliente externo | `graphql_client/client.py` | HTTP POST al API GraphQL, parseo de la respuesta JSON |
| Dominio | `models/producto.py` | Mapeo ORM a la tabla `productosgrpc` |
| Infraestructura | `database.py` | Conexión a `productos.db` en la raíz compartida |
| Transversal | `core/exceptions.py` | Errores gRPC tipados con `StatusCode` correcto |

---

## 3. Justificación de la arquitectura

### Feature-oriented para gRPC

La separación por capas con responsabilidades claras escala bien:

- Agregar una nueva entidad requiere: un `.proto`, regenerar stubs, un nuevo servicer y registrarlo en `server.py`. El resto del código no se toca.
- El servicer no conoce detalles del protocolo gRPC (solo implementa métodos); `grpcio` maneja la serialización y el transporte.
- El cliente GraphQL está aislado en su propio paquete (`graphql_client/`), con una interfaz simple (`listar_productos_graphql() -> List[dict]`). El servicer no conoce los detalles HTTP de esa llamada.

### BD compartida en la raíz

`productos.db` vive en `u4-api-rest-graphql-grpc/` (raíz del repositorio). Ambos proyectos apuntan a ese mismo archivo con rutas absolutas calculadas desde `database.py`. Cada proyecto opera en su propia tabla (`productosgrpc` / `productosgraphql`), lo que evita conflictos de esquema y permite demostrar la independencia de cada servicio.

---

## 4. Por qué gRPC + protobuf + grpcio

### gRPC

Framework RPC de Google construido sobre **HTTP/2**:

- **Contrato primero**: el `.proto` es la fuente de verdad compartida entre cliente y servidor, en cualquier lenguaje.
- **Generación de código**: `grpc_tools.protoc` genera stubs tipados; elimina errores manuales de serialización.
- **Transporte HTTP/2**: multiplexado, cabeceras comprimidas, push del servidor.
- **Streaming bidireccional**: server streaming, client streaming y bidireccional son ciudadanos de primera clase.

### Protocol Buffers

- Serialización **binaria**, 3-10x más compacta que JSON.
- Fuertemente tipada: errores de tipo se detectan en generación, no en ejecución.
- Retro-compatible: agregar campos con números mayores no rompe clientes viejos.

### grpcio (Python)

- Implementación oficial para Python.
- `grpcio-tools` incluye el compilador `protoc` como módulo Python (sin binarios externos).
- `ThreadPoolExecutor` en el servidor maneja concurrencia sin código adicional.

---

## 5. Integración con el API GraphQL

### Por qué gRPC llama a GraphQL

Demuestra que ambos protocolos pueden coexistir y complementarse: gRPC es óptimo para comunicación interna de alta performance, mientras que GraphQL expone una interfaz flexible al exterior. Un servicio gRPC puede consumir datos de una API GraphQL como fuente externa sin acoplarse a su implementación interna.

### Arquitectura del cliente HTTP integrado

```
ProductoServicer.ListProductosGraphQL(request, context)
    │
    ▼
graphql_client/client.py → listar_productos_graphql()
    │  construye payload JSON:
    │  { "query": "query { productos { id nombre descripcion precio } }" }
    │
    │  urllib.request.Request POST → http://localhost:8000/graphql
    │  [HTTP/1.1 + JSON]
    ▼
API GraphQL (producto-graphql, puerto 8000)
    │  Strawberry resuelve la query
    │  lee de tabla productosgraphql
    │  retorna JSON
    ▼
graphql_client/client.py
    │  parsea data["data"]["productos"]
    │  retorna List[dict]
    ▼
ProductoServicer
    │  convierte dicts → ProductoResponse (protobuf)
    │  retorna ProductoList al cliente gRPC
    ▼
Cliente gRPC (stub) → objeto Python tipado
```

### Por qué urllib en lugar de requests/httpx

Se usa `urllib.request` de la biblioteca estándar de Python para mantener el proyecto sin dependencias extra. Para un entorno de producción se recomendaría `httpx` (con soporte async) o `requests` con pool de conexiones.

### Manejo de errores de red

Si el servidor GraphQL no está disponible:
- `urllib.error.URLError` se captura y se convierte en `ConnectionError`.
- El servicer llama a `handle_grpc_error(context, internal_error(str(e)))`.
- El cliente gRPC recibe `StatusCode.INTERNAL` con el mensaje descriptivo.

---

## 6. Decisiones de diseño clave

### UpdateProducto con flags de actualización parcial

En proto3, todos los campos tienen valores por defecto (`0`, `""`, `false`). Si el cliente envía `precio=0.0`, es imposible distinguir "actualizar a cero" de "no envié este campo".

**Solución**: campos booleanos `update_nombre`, `update_descripcion`, `update_precio`. Solo se modifica un campo si su bandera es `true`. Este patrón es más explícito que `google.protobuf.FieldMask` y más simple de implementar.

### SessionLocal por petición RPC

Cada método RPC crea su propia sesión SQLAlchemy y la cierra en el bloque `finally`. Con `ThreadPoolExecutor`, cada hilo atiende una petición; una sesión por petición evita problemas de concurrencia y sigue el patrón recomendado por SQLAlchemy.

### Manejo de errores con códigos gRPC nativos

Los errores de negocio se convierten en `StatusCode` de gRPC mediante `context.set_code()` y `context.set_details()`. El cliente puede inspeccionar el código y el mensaje sin parsear JSON.

| Error de negocio | StatusCode gRPC |
|-----------------|-----------------|
| ID no encontrado | `NOT_FOUND` (5) |
| Nombre vacío / precio negativo | `INVALID_ARGUMENT` (3) |
| Error de BD o red | `INTERNAL` (13) |

---

## 7. Flujo de operaciones

### Operación local: GetProducto(id=1)

```
Cliente gRPC
    │── stub.GetProducto(ProductoId(id=1))
    │   [serializa a binario protobuf]
    │
    │  [HTTP/2 frame → localhost:50051]
    ▼
ProductoServicer.GetProducto(request, context)
    │  db.query(Producto).filter(id==1).first()
    │  → producto encontrado
    │  → _modelo_a_response(producto) → ProductoResponse
    │
    │  [HTTP/2 frame de respuesta, binario protobuf]
    ▼
Cliente gRPC
    │  [deserializa → objeto Python tipado]
    ▼
Datos disponibles en el cliente

Si el producto NO existe:
    context.set_code(StatusCode.NOT_FOUND)
    context.set_details("Producto con id 1 no encontrado")
    → cliente recibe grpc.RpcError con code=NOT_FOUND
```

### Operación integrada: ListProductosGraphQL

```
Cliente gRPC
    │── stub.ListProductosGraphQL(Empty())
    ▼
ProductoServicer.ListProductosGraphQL(request, context)
    ▼
graphql_client/client.py → listar_productos_graphql()
    │  POST http://localhost:8000/graphql
    │  body: { "query": "query { productos { id nombre descripcion precio } }" }
    ▼
API GraphQL (producto-graphql)
    │  Strawberry resuelve → SELECT de productosgraphql
    │  retorna JSON: { "data": { "productos": [...] } }
    ▼
graphql_client/client.py
    │  parsea JSON → List[dict]
    ▼
ProductoServicer
    │  convierte a ProductoResponse[] → ProductoList
    ▼
Cliente gRPC → lista de productos de productosgraphql
```

---

## 8. Comparación gRPC vs GraphQL

| Característica | gRPC (este proyecto) | GraphQL |
|----------------|---------------------|---------|
| **Protocolo** | HTTP/2 (binario) | HTTP/1.1 o HTTP/2 (JSON) |
| **Serialización** | Protocol Buffers (compacto, rápido) | JSON (legible, verboso) |
| **Contrato** | `.proto` — schema-first estricto | Schema SDL — flexible |
| **Tipado** | Fuertemente tipado + generación de código | Fuertemente tipado, sin generación por defecto |
| **Consultas flexibles** | No (operaciones fijas por RPC) | Sí (cliente elige los campos) |
| **Streaming** | Nativo (4 modos) | Suscripciones via WebSocket |
| **Soporte en browsers** | Limitado (requiere gRPC-Web + proxy) | Nativo (HTTP + JSON) |
| **Herramientas de debug** | grpcurl, BloomRPC | GraphiQL, Apollo Studio |
| **Rendimiento** | Alto (binario + HTTP/2 multiplexado) | Medio-alto (puede tener N+1) |
| **Interoperabilidad** | Cualquier lenguaje con plugin protoc | Cualquier cliente HTTP |
| **Ideal para** | Microservicios internos, IoT, alto throughput | APIs públicas, frontends, BFF |

---

## 9. Cuándo usar gRPC vs GraphQL

### Usa gRPC cuando:

- **Microservicios internos**: backend-a-backend donde el rendimiento binario importa.
- **Contratos estrictos**: el `.proto` es la API pública; cualquier cambio es un contrato formal.
- **Streaming en tiempo real**: telemetría, logs, estado continuo.
- **Baja latencia y alto throughput**: IoT, sistemas financieros, gaming.
- **Múltiples lenguajes**: un `.proto` genera stubs en Go, Java, Python, Rust, etc.

### Usa GraphQL cuando:

- **APIs públicas o para terceros**: flexibilidad para elegir campos.
- **Clientes web y móviles**: browsers consumen HTTP+JSON nativamente.
- **Datos relacionales complejos**: el grafo de tipos modela bien las relaciones.
- **Exploración y documentación**: GraphiQL permite explorar sin código adicional.
- **BFF**: un endpoint que diferentes frontends consultan pidiendo solo lo que necesitan.

```
¿Comunicación interna backend-a-backend?  ──► gRPC
¿API pública consumida desde browsers?    ──► GraphQL / REST
¿Streaming real bidireccional?            ──► gRPC
¿Consultas de datos flexibles?            ──► GraphQL
¿Latencia y rendimiento críticos?         ──► gRPC
¿Facilidad de exploración y debugging?    ──► GraphQL
¿Múltiples lenguajes de programación?     ──► gRPC (generación de stubs)
```

---

## 10. Ventajas y desventajas de gRPC

### Ventajas

**Rendimiento**
Protocol Buffers produce mensajes 5-10x más pequeños que JSON. HTTP/2 multiplexado elimina el head-of-line blocking de HTTP/1.1 y permite múltiples streams sobre una conexión TCP.

**Contrato estricto**
El `.proto` es la definición formal de la API. Los stubs generados garantizan que cliente y servidor hablen el mismo idioma en tiempo de compilación, no de ejecución.

**Generación de código multilenguaje**
Un solo `.proto` genera stubs en +12 lenguajes oficiales (Go, Java, C++, Python, Rust, Node.js, etc.), eliminando errores de integración entre equipos poliglota.

**Streaming nativo**
Soporta 4 patrones de comunicación:
- Unary (request/response) — equivalente a REST
- Server streaming — logs, datos continuos
- Client streaming — upload por chunks
- Bidireccional streaming — chat, colaboración en tiempo real

**Cancelación y timeouts nativos**
El protocolo propaga deadlines y cancelaciones automáticamente a través de la cadena de servicios.

### Desventajas

**No legible por humanos**
Los mensajes binarios no se inspeccionan con `curl` o el inspector del browser sin herramientas especializadas (grpcurl, BloomRPC).

**Soporte limitado en browsers**
Los browsers no soportan HTTP/2 raw con trailers gRPC. Requiere gRPC-Web (subconjunto) + proxy (Envoy, grpc-gateway).

**Curva de aprendizaje**
Requiere entender el ecosistema protobuf: tipos específicos (int32, sint32, fixed32), numeración de campos, compatibilidad retroactiva, generación de stubs.

**Infraestructura de red**
Algunos proxies, load balancers y firewalls antiguos no soportan HTTP/2, complicando el despliegue en entornos heredados.

**Herramientas de documentación menos maduras**
No existe un equivalente de Swagger/OpenAPI tan extendido. gRPC Reflection ayuda, pero no es universal ni tan visual.
