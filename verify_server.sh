#!/bin/bash

SERVER_CONTAINER=${SERVER_CONTAINER:-server}
SERVER_PORT=${SERVER_PORT:-5678}
NC_TIMEOUT=${NC_TIMEOUT:-1}
MESSAGE="Hello World"
NETWORK=tp-nivelador_default
CLIENT_IMAGE=${CLIENT_IMAGE:-tp-nivelador-client_0}

RESPONSE=$(
    docker run --rm \
        --network "$NETWORK" \
        --entrypoint sh \
        -e MESSAGE="$MESSAGE" \
        -e SERVER_HOST="$SERVER_CONTAINER" \
        -e SERVER_PORT="$SERVER_PORT" \
        -e NC_TIMEOUT="$NC_TIMEOUT" \
        "$CLIENT_IMAGE" \
        -c 'echo "$MESSAGE" | nc -w "$NC_TIMEOUT" "$SERVER_HOST" "$SERVER_PORT"' || true
)

if [ "$RESPONSE" = "$MESSAGE" ]; then
    echo "Success: server echoed '${RESPONSE}'"
else
    echo "Fail: expected '${MESSAGE}', got '${RESPONSE:-<empty>}'"
    exit 1
fi
