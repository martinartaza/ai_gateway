# AI Gateway

Servicio centralizado de IA para uso interno. Recibe texto, lo envía a un modelo de lenguaje local y devuelve la respuesta. No contiene lógica de negocio ni memoria de conversaciones — es un proxy stateless reutilizable por múltiples proyectos.

## Cómo funciona

```mermaid
sequenceDiagram
    participant C as Cliente<br/>(Magento / ERP / etc.)
    participant G as FastAPI<br/>AI Gateway
    participant DB as MySQL
    participant O as Ollama
    participant M as Modelo LLM<br/>(Qwen 2.5 0.5B)

    C->>G: POST /chat {system, prompt}
    G->>G: Valida API key
    G->>G: Aplica rate limit
    G->>O: POST /v1/chat/completions
    O->>M: Inferencia
    M-->>O: Texto generado
    O-->>G: {choices, usage}
    G->>DB: Registra request + métricas
    G-->>C: {response, tokens, duration_ms}
```

Cada proyecto consumidor construye sus propios prompts y mantiene su propio historial de conversación. El gateway solo ejecuta la inferencia.

## Endpoints

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `POST` | `/chat` | API Key | Envía un prompt al modelo |
| `GET` | `/health` | — | Estado del servicio y del LLM |
| `GET` | `/metrics` | Admin key | Estadísticas de uso del día |

### POST /chat

```bash
curl -X POST https://ai.sebastianartaza.com/chat \
  -H "Authorization: Bearer TU_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "system": "Eres un asistente de e-commerce. Extrae el producto mencionado.",
    "prompt": "Hola, tienen alimento para perro pequeño?"
  }'
```

```json
{
  "response": "El producto es \"alimento para perro pequeño\".",
  "tokens": 60,
  "duration_ms": 201
}
```

### GET /health

```json
{
  "status": "ok",
  "model": "qwen2.5:0.5b",
  "llama_cpp": "running"
}
```

## Instalación

### Requisitos
- Docker con el plugin Compose
- Red `traefik` externa ya creada en el host

### Pasos

```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores reales

# 2. Levantar Ollama y descargar el modelo
docker compose up -d ollama
bash pull_model.sh

# 3. Levantar todos los servicios
docker compose up -d

# 4. Crear las tablas en MySQL (solo la primera vez)
docker compose exec web python init_db.py
```

### Crear un proyecto (API key)

Las API keys se gestionan directamente en MySQL:

```bash
docker compose exec mysql mysql -uroot -p ai_gateway -e \
  "INSERT INTO projects (name, api_key, enabled, rate_limit)
   VALUES ('nombre-proyecto', 'clave-secreta-aqui', 1, '60/minute');"
```

## Cambiar el modelo

El gateway es agnóstico al modelo. Ollama gestiona los modelos disponibles — para cambiar solo hay que:

1. Descargar el nuevo modelo
2. Actualizar dos variables en `.env`
3. Reiniciar el container `web`

```bash
# 1. Descargar el modelo en Ollama
docker compose exec ollama ollama pull NOMBRE_MODELO

# 2. Actualizar .env
LLM_MODEL_NAME=NOMBRE_MODELO

# 3. Reiniciar
docker compose up -d web
```

### Modelos disponibles con Ollama

| Modelo | `.env` `LLM_MODEL_NAME` | RAM aprox. | Ideal para |
|--------|------------------------|-----------|------------|
| Qwen 2.5 0.5B *(actual)* | `qwen2.5:0.5b` | ~600 MB | Extracción, clasificación simple |
| Qwen 2.5 1.5B | `qwen2.5:1.5b` | ~1.5 GB | Mejor comprensión, misma velocidad |
| Qwen 2.5 3B | `qwen2.5:3b` | ~2.5 GB | Respuestas más elaboradas |
| Llama 3.2 1B | `llama3.2:1b` | ~1.3 GB | Buena alternativa en inglés/español |
| Llama 3.2 3B | `llama3.2:3b` | ~2.5 GB | Balance calidad/velocidad |
| Mistral 7B | `mistral:7b` | ~5 GB | Alta calidad (requiere más RAM) |

> El servidor objetivo tiene 8 GB de RAM. Modelos de hasta 3B corren cómodos. Mistral 7B es el límite práctico.

### Cambiar a una API externa (Groq, OpenAI)

La interfaz `/v1/chat/completions` es compatible con cualquier proveedor OpenAI-compatible. Para usar Groq por ejemplo:

```env
LLM_BASE_URL=https://api.groq.com/openai
LLM_MODEL_NAME=llama-3.1-8b-instant
```

Y agregar el header de autenticación editando `app/llm.py`:

```python
headers={"Authorization": f"Bearer {settings.llm_api_key}"}
```

Los proyectos consumidores no necesitan ningún cambio al migrar entre modelos o proveedores.

## Variables de entorno

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `DATABASE_URL` | Conexión MySQL | `mysql+pymysql://root:changeme@mysql/ai_gateway` |
| `MYSQL_ROOT_PASSWORD` | Password MySQL (usado por Docker) | — |
| `LLM_BASE_URL` | URL base del backend LLM | `http://ollama:11434` |
| `LLM_MODEL_NAME` | Nombre del modelo en Ollama | `qwen2.5:0.5b` |
| `DEFAULT_RATE_LIMIT` | Límite de requests por API key | `60/minute` |
| `LOG_RETENTION_DAYS` | Días que se guardan los logs | `30` |
| `METRICS_API_KEY` | Clave para acceder a `/metrics` | — |

## Desarrollo local

```bash
# Activar entorno virtual
workon ia_gateway

# Servidor con hot reload
uvicorn app.main:app --reload
```

## Tests

Los tests usan SQLite en memoria y mockean el LLM — no requieren MySQL ni Ollama corriendo.

```bash
workon ia_gateway

# Todos los tests
pytest

# Un archivo específico
pytest tests/test_chat.py -v

# Un test específico
pytest tests/test_chat.py::test_chat_success -v

# Con output detallado y sin captura de prints
pytest -v -s

# Solo los tests que fallaron en la última ejecución
pytest --lf
```
