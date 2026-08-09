import csv

from services.server.src_frozen.lottery import Lottery, Bet
from .utils import docker, docker_compose
from .test_case import TestCase

DOCKER_COMPOSE_PATH = "docker-compose.yaml"


class OutputFiles(TestCase):
    title = "winners list in output files"

    @staticmethod
    def _verify_client_output(client_service):
        client_name = client_service["container_name"]
        input_file = "." + docker_compose.find_environment_variable(
            client_service, "INPUT_FILE"
        )
        output_file = "." + docker_compose.find_environment_variable(
            client_service, "OUTPUT_FILE"
        )
        agency_id = int(
            docker_compose.find_environment_variable(client_service, "AGENCY_ID")
        )
        lottery = Lottery(storage_path=None)

        expected = set()
        with open(input_file, newline="") as f:
            for row in csv.reader(f):
                if not row:
                    continue

                [first_name, last_name, document, birthdate, number] = row
                bet = Bet(
                    agency_id,
                    first_name,
                    last_name,
                    int(document),
                    birthdate,
                    int(number),
                )
                if lottery.has_won(bet):
                    expected.add(tuple(row))

        actual = set()
        with open(output_file, newline="") as f:
            for row in csv.reader(f):
                if not row:
                    continue
                actual.add(tuple(row))

        if expected - actual:
            raise AssertionError(f"Lottery winners mismatch for {client_name}")

    @staticmethod
    def _test() -> None:
        services = docker_compose.read(DOCKER_COMPOSE_PATH)["services"]
        client_services_names = docker_compose.find_services_by_context(
            services, "client"
        )

        zero_exit_code_count = docker.await_containers(client_services_names)
        if zero_exit_code_count != len(client_services_names):
            raise ValueError("One or more clients exited with an error code")

        for client_name in client_services_names:
            OutputFiles._verify_client_output(services[client_name])

    @staticmethod
    def test() -> None:
        OutputFiles.with_docker_run(DOCKER_COMPOSE_PATH, OutputFiles._test)
