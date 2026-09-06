from os import remove
from .utils import docker, docker_compose
from time import sleep
from .test_case import TestCase
from utils import shell_cmd, agency_file_generator

DOCKER_COMPOSE_PATH = "./tests/compose_files/docker-compose-memory-profile.yaml"

INPUT_FILE_PATH = "input/test-data.csv"

POLLING_AWAIT_SECONDS = 2
MEDIUM_FILE_ITEM_COUNT = 1000  # ~30Kb
LARGE_FILE_ITEM_COUNT = 1000 * MEDIUM_FILE_ITEM_COUNT  # ~30Mb
PROFILE_DIFF_THRESHOLD_BYTES = 8388608  # 8Mb


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
        MemoryProfile.await_net_io_stop(client_service_name, POLLING_AWAIT_SECONDS)
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

        if abs(profile2 - profile1) > PROFILE_DIFF_THRESHOLD_BYTES:
            raise ValueError(
                f"Difference in memory profiles is too big: {profile1}B vs {profile2}B"
            )
