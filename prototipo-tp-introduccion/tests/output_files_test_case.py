import csv

from services.server.src_frozen.lottery import Lottery, Bet
from .utils import docker, docker_compose
from .test_case import TestCase


class OutputFiles(TestCase):
    name = "output-files"

    def _verify_client_output(self, client_service):
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

    def test(self, log, docker_compose_path) -> None:
        try:
            services = docker_compose.read(docker_compose_path)["services"]
            client_services_names = docker_compose.find_services_by_context(
                services, "client"
            )

            log(f"Awaiting client containers to exit")
            docker.up()
            zero_exit_code_count = docker.await_containers(client_services_names)
            if zero_exit_code_count != len(client_services_names):
                raise ValueError("One or more clients exited with an error code")

            for client_name in client_services_names:
                self._verify_client_output(services[client_name])
                log(f"Lottery winners match for {client_name}")
        finally:
            docker.down()
