#!/bin/bash

# This script is used to initialize the docker-compose environment for the project.

CLIENTES="$1"
SERVER_PORT=5678
FILE_NAME="docker-compose.yaml"
BATCH_SIZE=500
AGENCY_QUORUM_MIN=3

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
      - AGENCY_QUORUM_MIN=$AGENCY_QUORUM_MIN

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
      - ./input:/input
      - ./output:/output
    environment:
      - AGENCY_ID=$i
      - SERVER_HOST=server
      - SERVER_PORT=$SERVER_PORT
      - INPUT_FILE=/input/input-$i.csv
      - OUTPUT_FILE=/output/output-$i.csv
      - BATCH_SIZE=$BATCH_SIZE
EOF
done
