#!/usr/bin/env bash
# Descarga el modelo dentro del contenedor Ollama.
# Ejecutar después de: docker compose up -d ollama

set -e

echo "Descargando qwen2.5:3b en Ollama (~2 GB)..."
docker exec ai_gateway_ollama ollama pull qwen2.5:3b
echo "Listo. Podés levantar el resto: docker compose up -d"
