#!/usr/bin/env bash
# Descarga el modelo dentro del contenedor Ollama.
# Ejecutar después de: docker compose up -d ollama

set -e

echo "Descargando qwen2.5:0.5b en Ollama (~400 MB)..."
docker exec ai_gateway_ollama ollama pull qwen2.5:0.5b
echo "Listo. Podés levantar el resto: docker compose up -d"
