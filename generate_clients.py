#!/usr/bin/env python3
"""Regenera el docker-compose.yaml con n clientes"""

import sys

SERVER_HOST = "server"
SERVER_PORT = 5678
CLIENTS_START = 0
OUTPUT_FILE = "docker-compose.yaml"


def build_client(i):
    return f"""  client_{i}:
    build:
      context: ./services/client
      dockerfile: Dockerfile
    container_name: client_{i}
    depends_on:
      - server
    environment:
      - AGENCY_ID={i}
      - SERVER_HOST={SERVER_HOST}
      - SERVER_PORT={SERVER_PORT}
"""


def generate_docker_compose(content):
    with open(OUTPUT_FILE, "w") as f:
        f.write(content)


def generate(n, start=CLIENTS_START):
    lines = []
    lines.append("services:")
    lines.extend(generate_server_lines())
    for i in range(start, start + n):
        lines.append(build_client(i).rstrip("\n"))
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def generate_server_lines():
    server_lines = []
    server_lines.append("  server:")
    server_lines.append("    build:")
    server_lines.append("      context: ./services/server")
    server_lines.append("      dockerfile: Dockerfile")
    server_lines.append("    container_name: server")
    server_lines.append("    environment:")
    server_lines.append("      - PYTHONUNBUFFERED=1")
    server_lines.append(f"      - SERVER_HOST={SERVER_HOST}")
    server_lines.append(f"      - SERVER_PORT={SERVER_PORT}")
    server_lines.append("")
    return server_lines


def check_params():
    if len(sys.argv) < 2:
        print("Uso: python generate_clients.py <n> [start]")
        sys.exit(1)
    n = int(sys.argv[1])
    start = int(sys.argv[2]) if len(sys.argv) > 2 else CLIENTS_START
    return n, start


def main():
    n, start = check_params()
    content = generate(n, start)
    generate_docker_compose(content)
    print(f"Generados {n} clientes (client_{start}..client_{start + n - 1}) en {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
