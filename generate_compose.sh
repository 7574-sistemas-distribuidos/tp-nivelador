#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <amount_of_clients>"
    exit 1
fi

AMOUNT_OF_CLIENTS=$1
OUTPUT_FILE="docker-compose.yaml"

cat >"$OUTPUT_FILE" <<EOF
services:
    server:
        build:
            context: ./services/server
            dockerfile: Dockerfile
        container_name: server
        ports:
            -   "5678:5678"
        environment:
            - PYTHONUNBUFFERED=1
            - SERVER_HOST=server
            - SERVER_PORT=5678
EOF

for i in $(seq 0 $((AMOUNT_OF_CLIENTS - 1))); do
    cat >>"$OUTPUT_FILE" <<EOF

    client_${i}:
        build:
            context: ./services/client
            dockerfile: Dockerfile
        container_name: client_${i}
        depends_on:
            - server
        environment:
            - AGENCY_ID=${i}
            - SERVER_HOST=server
            - SERVER_PORT=5678
EOF
done

echo "Generated ${OUTPUT_FILE} with ${AMOUNT_OF_CLIENTS} clients"
