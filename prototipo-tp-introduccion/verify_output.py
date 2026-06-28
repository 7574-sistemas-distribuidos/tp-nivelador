import csv
import os
import sys
import yaml
import logging
import subprocess
from pathlib import Path

from lottery.lottery import Lottery
from lottery.bet import Bet

DOCKER_FILE_PATH = "./docker-compose.yaml"


class ClientValidationError(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def run(
    cmd: list[str],
    cwd: str | None = None,
    capture: bool = False,
    check: bool = False,
    shell: bool = False,
    env: dict | None = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=check,
        shell=shell,
        env=env,
    )


def docker_await_client_containers(client_services_name):
    result = run(["docker", "container", "wait"] + client_services_name, capture=True)

    zero_exit_code_count = 0
    for char in result.stdout.decode("utf-8"):
        if char == "0":
            zero_exit_code_count += 1

    if zero_exit_code_count != len(client_services_name):
        raise ClientValidationError("One or more clients exited with an error code")


def find_environment_variable(environment_variables, target_environment_variable):
    for environment_variable in environment_variables:
        [name, value] = environment_variable.split("=")
        if name == target_environment_variable:
            return value
    return None


def verify_client_output(client_service):
    client_name = client_service["container_name"]
    environment = client_service["environment"]
    input_file = "." + find_environment_variable(environment, "INPUT_FILE")
    output_file = "." + find_environment_variable(environment, "OUTPUT_FILE")
    agency_id = find_environment_variable(environment, "AGENCY_ID")

    if not input_file or not output_file:
        raise ClientValidationError("Bad environment variable config")

    lottery = Lottery(storage_path=None)

    expected = set()
    with open(input_file, newline="") as f:
        for row in csv.reader(f):
            if not row:
                continue
            bet = Bet(agency_id, *row)
            if lottery.has_won(bet):
                expected.add(tuple(row))

    actual = set()
    with open(output_file, newline="") as f:
        for row in csv.reader(f):
            if not row:
                continue
            actual.add(tuple(row))

    if expected - actual:
        raise ClientValidationError(f"Lottery winners mismatch for {client_name}")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )
    os.makedirs("output", exist_ok=True)

    try:
        with open(DOCKER_FILE_PATH) as f:
            services = yaml.safe_load(f)["services"]

        client_service_names = [
            service for service in services if "client" in services[service]["build"]["context"]
        ]

        logging.info("Awaiting client containers to exit...")
        docker_await_client_containers(client_service_names)

        logging.info("Awaiting client containers to exit...")
        for client_name in client_service_names:
            verify_client_output(services[client_name])
            logging.info(f"Lottery winners match for {client_name}")
    except ClientValidationError as e:
        logging.error(e.message)
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
