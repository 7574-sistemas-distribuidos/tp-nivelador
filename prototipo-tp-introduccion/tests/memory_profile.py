from os import remove
from .utils import docker, docker_compose
from time import sleep
from .test_case import TestCase
from utils import shell_cmd, agency_file_generator

DOCKER_COMPOSE_PATH = "docker-compose-memory-profile.yaml"

INPUT_FILE_PATH = "input/test-data.csv"
MEDIUM_FILE_ITEM_COUNT = 10000
LARGE_FILE_ITEM_COUNT = 100000

PROFILE_DIFF_THRESHOLD_BYTES = 2000000


class MemoryProfile(TestCase):
    title = "memory profile"
    error_hint = (
        "Client's memory profile shouldn't grow drastically with larger datasets"
    )

    @staticmethod
    def _create_agency_file(item_count: int) -> None:
        agency_file_generator.generate(INPUT_FILE_PATH, item_count)

    @staticmethod
    def _remove_agency_file() -> None:
        remove(INPUT_FILE_PATH)

    @staticmethod
    def _get_peak_memory_in_bytes(client_service_name) -> int:
        MemoryProfile.await_net_io_stop(client_service_name)
        peak_mem = docker.get_container_peak_memory_in_bytes(client_service_name)
        return peak_mem

    @staticmethod
    def test() -> None:
        docker_compose_content = docker_compose.read(DOCKER_COMPOSE_PATH)
        services = docker_compose_content["services"]

        client_service_name = docker_compose.find_services_by_context(
            services, "client"
        )[0]

        MemoryProfile._create_agency_file(MEDIUM_FILE_ITEM_COUNT)

        profile1 = MemoryProfile.with_docker_run(
            DOCKER_COMPOSE_PATH,
            lambda: MemoryProfile._get_peak_memory_in_bytes(client_service_name),
        )

        MemoryProfile._create_agency_file(LARGE_FILE_ITEM_COUNT)
        profile2 = MemoryProfile.with_docker_run(
            DOCKER_COMPOSE_PATH,
            lambda: MemoryProfile._get_peak_memory_in_bytes(client_service_name),
        )

        MemoryProfile._remove_agency_file()

        if profile2 - profile1 > PROFILE_DIFF_THRESHOLD_BYTES:
            raise ValueError(
                f"Difference in memory profiles is too big: {profile1}B vs {profile2}B"
            )
