import time

from .utils import docker, docker_compose
from .test_case import TestCase

DOCKER_COMPOSE_PATH = "docker-compose-no-agency-quorum.yaml"
SECONDS_BEFORE_CONCURRENCY_CHECK = 5


class Concurrency(TestCase):
    title = "spawned processes/threads"

    @staticmethod
    def _test() -> None:
        docker_compose_content = docker_compose.read(DOCKER_COMPOSE_PATH)
        services = docker_compose_content["services"]
        server_service_name = docker_compose.find_services_by_context(
            services, "server"
        )[0]
        time.sleep(SECONDS_BEFORE_CONCURRENCY_CHECK)
        server_pids = docker.get_container_pids(server_service_name)
        if server_pids < 2:
            raise ValueError(f"{server_service_name} runs on a single thread/process")

    @staticmethod
    def test() -> None:
        Concurrency.with_docker_run(DOCKER_COMPOSE_PATH, Concurrency._test)
