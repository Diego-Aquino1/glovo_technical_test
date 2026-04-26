# Asistente de Compromiso de Stock — Prueba Técnica Multiagente ERP

Sistema multi-agente basado en IA para responder preguntas de negocio sobre disponibilidad de stock, compromiso de entrega y reposiciones, integrando un ERP simulado mediante el protocolo MCP.

**Stack:** FastAPI · LangChain · FastMCP · PostgreSQL · Redis · Docker · uv · Alembic · Ruff

---

## Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│                         docker-compose                           │
│                                                                  │
│  ┌──────────────┐      ┌──────────────────────────────────────┐  │
│  │   frontend   │─────▶│          api-gateway  :8000          │  │
│  │  Nginx :3000 │      │  FastAPI · API Key Auth · Proxy      │  │
│  └──────────────┘      └────────────────┬─────────────────────┘  │
│                                         │ HTTP interno           │
│                         ┌───────────────▼─────────────────────┐  │
│                         │       orchestrator  :8003           │  │
│                         │  LangChain create_agent             │  │
│                         │  MultiServerMCPClient + interceptors│  │
│                         │  Redis chat history                 │  │
│                         │  LangSmith tracing                  │  │
│                         └───────────────┬─────────────────────┘  │
│                                         │ MCP Streamable HTTP    │
│                         ┌───────────────▼─────────────────────┐  │
│                         │        mcp-server  :8002            │  │
│                         │  FastMCP · 3 tools                  │  │
│                         │  Capa semántica · RBAC              │  │
│                         │  Sanitización · Auditoría → PG      │  │
│                         └───────────────┬─────────────────────┘  │
│                                         │ HTTP REST              │
│                         ┌───────────────▼─────────────────────┐  │
│                         │       erp-service  :8001            │  │
│                         │  FastAPI · SQLAlchemy async         │  │
│                         │  Alembic · Paginación               │  │
│                         └───────────────┬─────────────────────┘  │
│              ┌──────────────────────────▼──────────────────┐     │
│              │  postgres :5432  ·  redis :6379             │     │
│              └─────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
```

---

## Inicio rápido

```bash
cp .env.example .env

docker compose up --build

open http://localhost:3000
```

---

## Servicios y puertos


| Servicio       | Puerto | Descripción                        |
| -------------- | ------ | ---------------------------------- |
| `frontend`     | 3000   | Chat UI (Nginx + HTML/CSS/JS)      |
| `api-gateway`  | 8000   | Punto de entrada público (API Key) |
| `orchestrator` | 8003   | Agente LangChain + cliente MCP     |
| `mcp-server`   | 8002   | FastMCP con 3 tools de negocio     |
| `erp-service`  | 8001   | Mini ERP REST con paginación       |
| `postgres`     | 5432   | Base de datos principal            |
| `redis`        | 6379   | Historial de sesiones de chat      |


---

# Cuestionario Teórico

**1. ¿Cuáles son las ventajas de utilizar un API Gateway en una arquitectura de agentes distribuidos?**

Centraliza la autenticación, la API Key se valida una sola vez antes de que la request llegue a cualquier servicio interno. El gateway sobreescribe el `user_role` en el body, por lo que el cliente nunca puede autopromover sus privilegios. Además desacopla la URL pública de los servicios internos — si el orquestador cambia de puerto o escala, la interfaz pública no cambia. Todos los requests pasan por un único punto instrumentable con métricas, rate limiting y CORS.

---

**2. ¿Por qué es fundamental mapear el ERP a una capa semántica antes de pasarle los datos al agente?**

Los nombres técnicos del ERP (columnas como `qty_avail_phys_excl`, tablas como `t_stkdet_v2`) son ambiguos para el LLM y aumentan el riesgo de alucinaciones. La capa semántica traduce esos nombres a términos de negocio con descripciones claras, lo que reduce la ambigüedad y por tanto los errores. También actúa como contrato estable: si el ERP refactoriza internamente, solo cambia el schema semántico; el agente no se rompe.

---

**3. ¿Cómo garantizarías la trazabilidad y auditoría de las acciones de un agente autónomo?**

Con una tabla `audit_logs` append-only en PostgreSQL donde se registra por cada llamada a tool: sesión, rol, tool invocada, parámetros exactos, resumen del resultado, latencia y timestamp generado por la base de datos. El usuario de aplicación tiene revocados los permisos de UPDATE y DELETE sobre esa tabla, por lo que ningún proceso puede alterar registros ya escritos. LangSmith complementa con trazas completas del grafo del agente.

---

**4. ¿Cómo diseñarías el mecanismo de retry si una tool falla o devuelve un timeout?**

Máximo 3 reintentos con exponential backoff y jitter aleatorio. Solo se reintentan errores transitorios: errores de red y respuestas 5xx. Los errores 4xx son deterministas y no mejoran con reintentos. El jitter evita que varios agentes fallen y reintenten simultáneamente. Tras 3 fallos, la tool devuelve `{"status": "service_error"}` y el agente informa al usuario sin inventar la respuesta.

---

**5. Si el agente encadena 4 tools y la tercera falla, ¿cómo evitas que se pierda el trabajo anterior?**

Los resultados de las tools anteriores ya están en el historial de mensajes del agente y no se pierden aunque una posterior falle. El agente puede responder parcialmente con la información disponible, declarando explícitamente qué parte falta. El system prompt le instruye a nunca inventar la información ausente. Para flujos con efectos secundarios, cada tool podría persistir su resultado en Redis como checkpoint antes de continuar.

---

**6. ¿Cómo estructurarías el prompt del agente para que no alucine cuando una tool devuelve un resultado vacío?**

Con reglas explícitas en el system prompt: solo puede usar datos devueltos por las tools, nunca inferir ni estimar; si una tool devuelve vacío o cero, debe declarar ausencia de datos; si los datos son insuficientes para responder, debe decirlo y explicar qué falta. El prompt también define el DAG obligatorio de ejecución, por lo que el agente no puede saltarse pasos ni continuar sin datos válidos del paso anterior.

---

**7. ¿Cómo distinguirías entre "el producto no existe" y "el producto existe pero sin stock"?**

La primera tool del DAG, `get_article_info`, resuelve esta distinción devolviendo campos semánticamente distintos: `exists=false` cuando el artículo no está en el catálogo, `exists=true + is_obsolete=true` cuando está descatalogado, y `exists=true + is_obsolete=false` cuando es válido. Solo en este último caso el agente continúa y llama a `get_stock_availability`. Si esa segunda tool devuelve `total_available=0`, eso es un cuarto estado diferente: el producto existe y está activo pero no tiene stock.

---

**8. Si el ERP usa paginación en su API REST, ¿cómo garantizas el dataset completo dentro de una tool?**

El cliente HTTP implementa `get_all_pages()`: itera en bucle incrementando el número de página hasta que el campo `pages` del response indica que no hay más, o hasta que la página devuelta está vacía. Usa un tamaño de página de 100 para no sobrecargar el ERP. La condición de parada compara la cantidad acumulada con el campo `total` del response para evitar una request extra innecesaria.

---

**9. ¿Cómo versionarías el esquema semántico para que cambios en el ERP no rompan el agente?**

El archivo incluye un campo `version` con semver. Cambios PATCH (descripciones) son transparentes. Cambios MINOR (campos nuevos opcionales) son retrocompatibles. Cambios MAJOR (campos renombrados o eliminados) requieren validación previa en staging. El MCP Server valida al arrancar que todos los campos referenciados en las tools existen en el schema; si falta alguno, el contenedor no arranca, evitando errores silenciosos en producción.

---

**10. ¿Cómo implementarías RBAC para que el agente solo acceda a los datos autorizados por perfil?**

En dos niveles: el API Gateway asigna el `user_role` según la API Key y lo sobreescribe en el body — el cliente no puede cambiarlo. En el MCP Server, cada tool verifica que el rol tenga permiso antes de ejecutar. El `user_role` viaja desde el gateway hasta las tools mediante interceptores de contexto en el cliente MCP, sin pasar por el cuerpo del prompt del LLM.

---

**11. ¿Cómo mitigarías un ataque de Prompt Injection?**

Con cuatro defensas en capas: el MCP Server detecta keywords peligrosos (DROP, DELETE, UNION, etc.) en los parámetros de entrada y rechaza la llamada antes de ejecutar nada. El agente nunca genera SQL directamente — solo invoca tools con parámetros tipados, eliminando la superficie de ataque. El system prompt define una identidad fuerte y restringida. El parámetro `sku` tiene validación de formato estricta con regex; cualquier texto libre falla antes de llegar al ERP.

---

**12. ¿Cómo garantizarías que el agente nunca ejecute operaciones de escritura?**

En tres capas independientes: las tools del MCP Server solo hacen peticiones GET al ERP — no existe ninguna tool de escritura registrada. El ERP Service solo expone endpoints GET en sus routers FastAPI. A nivel de base de datos, el usuario de aplicación debería tener únicamente GRANT SELECT sobre las tablas de negocio; aunque alguien saltase las dos capas anteriores, PostgreSQL rechazaría la operación por falta de permisos.

---

**13. ¿Qué información incluirías en los logs de auditoría y cómo los protegerías de manipulación?**

Cada registro incluye: sesión, rol del usuario, tool invocada, parámetros exactos de entrada, resumen del resultado, latencia y timestamp. El timestamp y el UUID se generan en PostgreSQL, no en el cliente, por lo que no pueden falsificarse. La tabla es append-only: el usuario de aplicación tiene revocados UPDATE y DELETE, así que los registros existentes son inmutables.