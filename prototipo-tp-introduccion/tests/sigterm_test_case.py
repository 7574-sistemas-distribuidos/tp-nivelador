import time
import multiprocessing

from .utils import docker, docker_compose
from .test_case import TestCase

DOCKER_COMPOSE_PATH = "docker-compose-no-agency-quorum.yaml"
SECONDS_BEFORE_SIGTERM = 5


def _stop_service(client_service) -> None:
    time.sleep(SECONDS_BEFORE_SIGTERM)
    docker.stop([client_service])


class SigtermHandling(TestCase):
    title = "sigterm handling"
    error_hint = "The SIGTERM signal must be correctly handled as soon as possible and at any stage of the communication in both the clients and the server"

    @staticmethod
    def _test_stopping_service(service_name) -> None:
        stop_service_process = None
        try:
            stop_service_process = multiprocessing.Process(
                target=_stop_service, args=(service_name,)
            )
            stop_service_process.start()
            zero_exit_code_count = docker.await_containers([service_name])
            if zero_exit_code_count != 1:
                raise ValueError(f"{service_name} exited with an error code")
        finally:
            if stop_service_process:
                stop_service_process.join()

    @staticmethod
    def test() -> None:
        docker_compose_content = docker_compose.read(DOCKER_COMPOSE_PATH)
        services = docker_compose_content["services"]

        client_service_name = docker_compose.find_services_by_context(
            services, "client"
        )[0]
        SigtermHandling.with_docker_run(
            DOCKER_COMPOSE_PATH,
            lambda: SigtermHandling._test_stopping_service(client_service_name),
        )

        server_service_name = docker_compose.find_services_by_context(
            services, "server"
        )[0]
        SigtermHandling.with_docker_run(
            DOCKER_COMPOSE_PATH,
            lambda: SigtermHandling._test_stopping_service(server_service_name),
        )
