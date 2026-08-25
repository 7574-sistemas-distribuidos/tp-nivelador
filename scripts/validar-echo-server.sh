#!/usr/bin/env bash
#
# Valida el echo server sin exponer puertos al host y sin editar docker-compose.yaml.
#
# Levanta un container efimero de busybox sobre la misma network que crea Compose,
# le manda un mensaje al server con netcat y compara el eco recibido.
#
# Uso:
#   ./validar-echo-server.sh [mensaje]
#
# Variables de entorno:
#   COMPOSE_FILE     archivo de compose            (default: docker-compose.yaml)
#   SERVER_SERVICE   nombre del servicio del server (default: server)
#   SERVER_PORT      puerto del server             (default: 5678)
#   TIMEOUT          segundos de espera del eco    (default: 5)


COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yaml}"
COMPOSE_NETWORK="tp_0_network"
SERVER_SERVICE="${SERVER_SERVICE:-server}"
SERVER_PORT="${SERVER_PORT:-5678}"
TIMEOUT="${TIMEOUT:-5}"
NETCAT_IMAGE="busybox:latest"

MESSAGE="${1:-Hello World}"

log()  { printf '%s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

container_id="$(docker compose -f "$COMPOSE_FILE" ps -q "$SERVER_SERVICE" 2>/dev/null || true)"
[ -n "$container_id" ] || fail "el servicio '$SERVER_SERVICE' no esta corriendo"


log "network : $COMPOSE_NETWORK"
log "destino : ${SERVER_SERVICE}:${SERVER_PORT}"
log "mensaje : $MESSAGE"

docker image inspect "$NETCAT_IMAGE" >/dev/null 2>&1 || docker pull -q "$NETCAT_IMAGE" >/dev/null

set +e
echo_recibido="$(timeout "$((TIMEOUT + 10))" docker run --rm \
  --network "$COMPOSE_NETWORK" \
  -e MESSAGE="$MESSAGE" \
  "$NETCAT_IMAGE" \
  sh -c "printf '%s\\n' \"\$MESSAGE\" | timeout $TIMEOUT nc $SERVER_SERVICE $SERVER_PORT | head -n 1; exit 0" 2>/dev/null)"
run_status=$?
set -e

[ "$run_status" -ne 124 ] || fail "timeout: 'docker run' no termino a tiempo"


if [ "$echo_recibido" != "$MESSAGE" ]; then
  fail "el echo no coincide. esperado: '$MESSAGE' | recibido: '$echo_recibido'"
fi

log "recibido: $echo_recibido"
log "OK: el server devolvio el eco correctamente"
