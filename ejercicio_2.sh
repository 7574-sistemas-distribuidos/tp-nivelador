#!/usr/bin/env bash
set -euo pipefail

NETWORK_NAME="tp-nivelador_default"
SERVER_HOSTNAME="server"
PORT="5678"

docker run --rm --init --network "$NETWORK_NAME" busybox timeout 2 sh -c "echo 'Hello World' | nc $SERVER_HOSTNAME $PORT"
