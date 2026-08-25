#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<USAGE
Uso: $(basename "$0") <cantidad_clientes> [archivo_salida]

  cantidad_clientes  Cantidad de contenedores cliente a generar (entero >= 0).
  archivo_salida     Ruta del compose a generar (default: docker-compose.yaml).

Ejemplos:
  $(basename "$0") 5
  $(basename "$0") 10 docker-compose.dev.yaml
USAGE
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
    usage >&2
    exit 1
fi

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
    exit 0
fi

CLIENTS="$1"
OUTPUT="${2:-docker-compose.yaml}"

if ! [[ "$CLIENTS" =~ ^[0-9]+$ ]]; then
    echo "Error: '$CLIENTS' no es un entero valido." >&2
    exit 1
fi

SERVER_HOST="server"
SERVER_PORT="5678"
NETWORK_NAME="tp_0_network"

{
    cat <<YAML
services:
  server:
    build:
      context: ./services/server
      dockerfile: Dockerfile
    container_name: server
    ports:
      - "${SERVER_PORT}:${SERVER_PORT}"
    environment:
      - PYTHONUNBUFFERED=1
      - SERVER_HOST=${SERVER_HOST}
      - SERVER_PORT=${SERVER_PORT}
YAML

    for ((i = 0; i < CLIENTS; i++)); do
        cat <<YAML

  client_${i}:
    build:
      context: ./services/client
      dockerfile: Dockerfile
    container_name: client_${i}
    depends_on:
      - server
    environment:
      - AGENCY_ID=${i}
      - SERVER_HOST=${SERVER_HOST}
      - SERVER_PORT=${SERVER_PORT}
      - INPUT_FILE=/input/input-${i}.csv
      - OUTPUT_FILE=/output/output-${i}.csv
    volumes:
      - ./input:/input
      - ./output:/output
YAML
    done

    cat <<YAML

networks:
  default:
    name: ${NETWORK_NAME}
YAML
} > "$OUTPUT"

echo "Generado '$OUTPUT' con 1 servidor y ${CLIENTS} cliente(s)."
