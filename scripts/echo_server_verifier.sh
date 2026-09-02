#!/usr/bin/env bash
set -u

NETWORK="${NETWORK:-tp-nivelador_default}"
MESSAGE="Hello World"

response=$(docker run --rm --network "$NETWORK" busybox \
  sh -c "echo '$MESSAGE' | nc -w 3 server 5678")

if [[ "$response" == "$MESSAGE" ]]; then
  echo "PASS: server echoed '$response'"
  exit 0
else
  echo "FAIL: sent '$MESSAGE', got '$response'"
  exit 1
fi
