Necesito que me ayudes a construir DOS proyectos backend independientes en Python, 
ambos para realizar operaciones CRUD sobre una entidad "Producto", usando SQLite 
como base de datos y SQLAlchemy como ORM. Los proyectos son:

PROYECTO 1: API GraphQL con FastAPI + Strawberry + SQLAlchemy + SQLite  diseño orientado a feactures organizando por capacidades 
PROYECTO 2: Servicio gRPC con Python + grpcio + SQLAlchemy + SQLite diseño orientado a feactures organizando por capacidades 

═══════════════════════════════════════════════════════════════════
ENTIDAD "Producto" (idéntica en ambos proyectos)
═══════════════════════════════════════════════════════════════════
- id: int (autoincremental, clave primaria)
- nombre: str (obligatorio)
- descripcion: str (opcional)
- precio: float (obligatorio, >= 0)

═══════════════════════════════════════════════════════════════════
OPERACIONES CRUD requeridas en AMBOS proyectos
═══════════════════════════════════════════════════════════════════
1. Crear producto
2. Listar todos los productos
3. Obtener producto por id
4. Actualizar producto por id
5. Eliminar producto por id

═══════════════════════════════════════════════════════════════════
ARQUITECTURA / ORGANIZACIÓN DEL CÓDIGO (rúbrica exige modularidad)
═══════════════════════════════════════════════════════════════════
Cada proyecto debe estar organizado en paquetes/módulos claros:

PROYECTO GraphQL (carpeta: producto-graphql/)
producto-graphql/
├── app/
│   ├── __init__.py
│   ├── main.py                  # punto de entrada FastAPI + montaje de GraphQL
│   ├── database.py              # engine, SessionLocal, Base, get_db
│   ├── models/
│   │   ├── __init__.py
│   │   └── producto.py          # modelo SQLAlchemy
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── producto_schema.py   # tipos GraphQL (Strawberry)
│   ├── resolvers/
│   │   ├── __init__.py
│   │   ├── queries.py           # Query: productos, producto(id)
│   │   └── mutations.py         # Mutation: crear, actualizar, eliminar
│   └── core/
│       ├── __init__.py
│       └── exceptions.py        # manejo de errores
├── requirements.txt
├── .gitignore
└── README.md

PROYECTO gRPC (carpeta: producto-grpc/)
producto-grpc/
├── app/
│   ├── __init__.py
│   ├── server.py                # arranque del servidor gRPC
│   ├── database.py              # engine, SessionLocal, Base
│   ├── models/
│   │   ├── __init__.py
│   │   └── producto.py          # modelo SQLAlchemy
│   ├── services/
│   │   ├── __init__.py
│   │   └── producto_service.py  # implementación del Servicer (lógica CRUD)
│   ├── protos/
│   │   ├── producto.proto       # contrato gRPC
│   │   ├── producto_pb2.py      # generado
│   │   └── producto_pb2_grpc.py # generado
│   └── core/
│       ├── __init__.py
│       └── exceptions.py        # manejo de errores y códigos gRPC
├── client_test.py               # cliente de prueba para validar CRUD
├── requirements.txt
├── .gitignore
└── README.md

═══════════════════════════════════════════════════════════════════
REQUISITOS TÉCNICOS
═══════════════════════════════════════════════════════════════════
- Python 3.11+
- SQLite (archivo local productos.db en cada proyecto)
- SQLAlchemy 2.x como ORM (NO escribir SQL manual, todo vía ORM)
- La tabla se debe crear automáticamente al iniciar (Base.metadata.create_all)
- Manejo adecuado de errores:
    * GraphQL: lanzar excepciones tipadas, retornar mensajes claros
    * gRPC: usar context.set_code(grpc.StatusCode.NOT_FOUND / INVALID_ARGUMENT / INTERNAL)
- Validación de datos (precio >= 0, nombre no vacío)
- Cerrar la sesión de DB correctamente (try/finally o context manager)

GraphQL específico:
- Usar Strawberry GraphQL integrado con FastAPI
- Endpoint: http://localhost:8000/graphql
- Habilitar GraphiQL para pruebas en navegador
- Probarse también desde Postman/Insomnia (POST con query)

gRPC específico:
- Definir .proto con servicio ProductoService y mensajes:
    ProductoRequest, ProductoId, ProductoResponse, ProductoList, Empty
- Generar stubs con: 
    python -m grpc_tools.protoc -I./app/protos --python_out=./app/protos 
    --grpc_python_out=./app/protos ./app/protos/producto.proto
- Servidor en localhost:50051
- Incluir un client_test.py que pruebe los 5 métodos CRUD
  (también se puede probar con Postman/BloomRPC/grpcurl)

═══════════════════════════════════════════════════════════════════
ENTREGABLES QUE NECESITO QUE GENERES
═══════════════════════════════════════════════════════════════════
Por cada proyecto entrégame:

1. Todos los archivos .py con código completo y comentado
2. El archivo .proto (solo para gRPC)
3. requirements.txt con versiones
4. .gitignore (excluir venv/, __pycache__/, *.db, etc.)
5. README.md con:
   - Descripción del proyecto
   - Cómo instalar dependencias
   - Cómo ejecutar
   - Ejemplos de queries/mutations GraphQL o llamadas gRPC
   - Capturas/ejemplos de pruebas en Postman/Insomnia
6. ARCHIRECTURA.md con:
    - justificacion de arqutiectura
    - por que se usa esta tecnolia
    - comparacion de tecnologia vs la del otro proyecto y por que ese enfoque
    - ventajas y desventajas de esta tecnologia o proyecto  con respecto al otro proyecto

═══════════════════════════════════════════════════════════════════
ORDEN DE ENTREGA
═══════════════════════════════════════════════════════════════════
Empieza por el PROYECTO GraphQL completo (todos los archivos uno por uno, 
explicando brevemente cada uno). Cuando termine, pásame al PROYECTO gRPC.

Al final dame una documentacion con:
- Comandos exactos para correr cada proyecto desde cero
- Ejemplos de queries GraphQL listas para pegar en GraphiQL/Postman
- Ejemplos de llamadas gRPC con el client_test.py
- Sugerencias de qué mostrar en el video de máximo 15 min