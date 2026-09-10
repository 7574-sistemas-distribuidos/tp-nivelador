import sys
import yaml

def generate_compose(filename, count):


    compose_data = {
        "services": {
            "server": {
                "container_name": "server",
                "build": {
                    "context": "./services/server",
                    "dockerfile": "Dockerfile"
                },
                "environment": [
                    "PYTHONUNBUFFERED=1",
                    "SERVER_HOST=server",
                    "SERVER_PORT=5678",
                    "STORAGE_DIR=/tmp/bets.csv",
                    f"AGENCY_QUORUM_MIN={count}"
                ],
            }
        },
    }

    for i in range(1, int(count) + 1):
        name = f"client{i}"
        compose_data["services"][name] = {
            "container_name": name,
            "build": {
                "context": "./services/client",
                "dockerfile": "Dockerfile"
            },
            "environment": [
                f"AGENCY_ID={i}",
                "SERVER_HOST=server",
                "SERVER_PORT=5678",
                f"INPUT_FILE=/input/input-{i}.csv",
                f"OUTPUT_FILE=/output/winners-{i}.csv"
            ],
            "volumes": [
                f"./input:/input:ro",
                f"./output:/output:rw"
            ],
            "depends_on": ["server"]
        }

    with open(filename, 'w') as f:
        yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Faltan argumentos")
        sys.exit(1)
    generate_compose(sys.argv[1], sys.argv[2])