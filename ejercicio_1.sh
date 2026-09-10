#!/usr/bin/env bash
set -euo pipefail

ARCHIVO_OBJETIVO="docker-compose.yaml"
ARCHIVO_PLANTILLA="docker-compose.yaml.plantilla"

if [[ -z "${1-}" ]]; then
    echo "Error: Se requiere el número de clientes como argumento."
    exit 1
fi

N="$1"

if [[ ! -f "$ARCHIVO_PLANTILLA" ]]; then
    echo "Error: No se encontró el archivo plantilla ($ARCHIVO_PLANTILLA)"
    exit 1
fi

cp "$ARCHIVO_PLANTILLA" "$ARCHIVO_OBJETIVO"

for (( i=1; i<=N; i++ )); do
cat <<EOF >> "$ARCHIVO_OBJETIVO"

  client_$i:
    build:
      context: ./services/client
      dockerfile: Dockerfile
    container_name: client_$i
    depends_on:
      - server
    environment:
      - AGENCY_ID=$i
      - SERVER_HOST=server
      - SERVER_PORT=5678
      - INPUT_FILE=/input/input-$i.csv
      - OUTPUT_FILE=/output/output-$i.csv
      - BATCH_SIZE=8
    volumes:
      - ./input:/input:ro
      - ./output:/output
EOF
done
