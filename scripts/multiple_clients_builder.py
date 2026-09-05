import sys

## TODO: Refactor to not make this templates drift apart from the actual docker-compose.yml file
SERVER_TEMPLATE = """services:
  server:
    build:
      context: ./services/server
      dockerfile: Dockerfile
    container_name: server
    ports:
      - 5678:5678
    environment:
      - PYTHONUNBUFFERED=1
      - SERVER_HOST=server
      - SERVER_PORT=5678
"""

CLIENT_TEMPLATE = """
  {client_name}:
    build:
      context: ./services/client
      dockerfile: Dockerfile
    container_name: {container_name}
    depends_on:
      - server
    volumes:
      - ./input:/input:ro
      - ./output:/output
    environment:
      - AGENCY_ID={client_id}
      - SERVER_HOST=server
      - SERVER_PORT=5678
      - INPUT_FILE=/input/input-{client_id}.csv
      - OUTPUT_FILE=/output/output-{client_id}.csv
"""


def main(number_of_clients_to_create, output_file_path):
    client_registry = client_registry_from(number_of_clients_to_create)
    clients_content = clients_content_from(client_registry)

    with open(output_file_path, "w") as output_file:
        output_file.write(SERVER_TEMPLATE)
        output_file.write(clients_content)


def client_registry_from(number_of_clients_to_create):
    client_service_registry = {}
    for i in range(number_of_clients_to_create):
        client_name = f"client_{i}"
        container_name = f"client_{i}"
        client_id = f"{i}"
        client_service_registry[client_name] = {
            "container_name": container_name,
            "client_id": client_id,
        }

    return client_service_registry


def clients_content_from(client_registry):
    return "".join(
        CLIENT_TEMPLATE.format(client_name=client_name, **client_service)
        for client_name, client_service in client_registry.items()
    )


if __name__ == "__main__":
    if len(sys.argv) > 2:
        number_of_clients_to_create = int(sys.argv[1])
        output_file_path = sys.argv[2]
        main(number_of_clients_to_create, output_file_path)
        sys.exit(0)
    else:
        print(
            "Usage: python3 clients_builder.py "
            "<number_of_clients_to_create> <output_file_path>"
        )
        sys.exit(1)
