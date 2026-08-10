from .utils import docker, docker_compose
from .test_case import TestCase

DOCKER_COMPOSE_PATH = "docker-compose-no-agency-quorum.yaml"

class Concurrency(TestCase):
    title = "spawned processes/threads"
    error_hint = "The server should spawn and orchestrate threads or processes to handle clients requests"

    @staticmethod
    def _test() -> None:
        docker_compose_content = docker_compose.read(DOCKER_COMPOSE_PATH)
        services = docker_compose_content["services"]
        server_service_name = docker_compose.find_services_by_context(
            services, "server"
        )[0]
        Concurrency.await_net_io_stop(server_service_name)
        server_pids = docker.get_container_pids(server_service_name)
        if server_pids < 2:
            raise ValueError(f"{server_service_name} runs on a single thread/process")

    @staticmethod
    def test() -> None:
        Concurrency.with_docker_run(DOCKER_COMPOSE_PATH, Concurrency._test)
