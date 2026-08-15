import re
from .utils import docker, docker_compose
from .test_case import TestCase

DOCKER_COMPOSE_PATH_UNIT = "./docker-compose-batching-unit.yaml"
DOCKER_COMPOSE_PATH_BASE = "./docker-compose-batching-base.yaml"
DOCKER_COMPOSE_PATH_DOUBLE = "./docker-compose-batching-double.yaml"

EXPECTED_PACKET_RATIO_MIN = 1.5
EXPECTED_PACKET_RATIO_MAX = 2.2

FLOAT_REGEX = r"\d+\.\d+"


class Batching(TestCase):
    title = "batching"
    error_hint = "Batching implementations should take into account how batched bytes are written or transferred besides the way they are represented in the system"

    @staticmethod
    def _calc_packet_length_average(docker_compose_path: str) -> float:
        services = docker_compose.read(docker_compose_path)["services"]
        client_services_name = docker_compose.find_services_by_context(
            services, "client"
        )[0]
        packets_services_name = docker_compose.find_services_by_context(
            services, "packets"
        )[0]
        zero_exit_code_count = docker.await_containers([client_services_name])
        if zero_exit_code_count != 1:
            raise ValueError("One or more clients exited with an error code")

        packet_length_average = docker_compose.get_container_last_logs(
            docker_compose_path, packets_services_name, 1
        )
        return float(re.findall(FLOAT_REGEX, packet_length_average)[0])

    @staticmethod
    def test() -> None:
        packet_lenght_average_unit = Batching.with_docker_run(
            DOCKER_COMPOSE_PATH_UNIT,
            lambda: Batching._calc_packet_length_average(DOCKER_COMPOSE_PATH_UNIT),
        )
        packet_lenght_average_base = Batching.with_docker_run(
            DOCKER_COMPOSE_PATH_BASE,
            lambda: Batching._calc_packet_length_average(DOCKER_COMPOSE_PATH_BASE),
        )
        packet_length_average_double = Batching.with_docker_run(
            DOCKER_COMPOSE_PATH_DOUBLE,
            lambda: Batching._calc_packet_length_average(DOCKER_COMPOSE_PATH_DOUBLE),
        )
        packet_lenght_average_base_normalized = (
            packet_lenght_average_base - packet_lenght_average_unit
        )
        packet_lenght_average_double_normalized = (
            packet_length_average_double - packet_lenght_average_unit
        )
        packet_length_average_ratio = (
            packet_lenght_average_double_normalized
            / packet_lenght_average_base_normalized
        )

        if (
            packet_length_average_ratio < EXPECTED_PACKET_RATIO_MIN
            or packet_length_average_ratio > EXPECTED_PACKET_RATIO_MAX
        ):
            raise ValueError(
                f"Doubling the batching size does not affect the bet packet length {packet_length_average_double}/{packet_lenght_average_base_normalized}"
            )
