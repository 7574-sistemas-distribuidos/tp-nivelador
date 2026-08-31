#!/bin/bash

# This script is used to initialize the docker-compose environment for the project.

CLIENTES="$1"
SERVER_PORT=5678
FILE_NAME="docker-compose.yaml"

if [ -z "$CLIENTES" ] || [ "$CLIENTES" -le 0 ]; then
  echo "No client specified. Please provide the amount of clients as arguments."
  exit 1
fi

cat << EOF > $FILE_NAME
services:
  server:
    build:
      context: ./services/server
      dockerfile: Dockerfile
    container_name: server
    ports:
      - "$SERVER_PORT:$SERVER_PORT"
    environment:
      - PYTHONUNBUFFERED=1
      - SERVER_HOST=server
      - SERVER_PORT=$SERVER_PORT

EOF

for ((i=0; i<CLIENTES; i++)); do
  cat << EOF >> $FILE_NAME
  client_$i:
    build:
      context: ./services/client
      dockerfile: Dockerfile
    container_name: client_$i
    depends_on:
      - server
    volumes:
      - ./input:/app/input
      - ./output:/app/output
    environment:
      - AGENCY_ID=$i
      - SERVER_HOST=server
      - SERVER_PORT=$SERVER_PORT
EOF
done
