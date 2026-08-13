from .utils import docker, docker_compose
from .test_case import TestCase

DOCKER_COMPOSE_PATH = "docker-compose-no-agency-quorum.yaml"


class SigtermHandling(TestCase):
    title = "sigterm handling"
    error_hint = "The SIGTERM signal must be correctly handled as soon as possible and at any stage of the communication in both the clients and the server"

    @staticmethod
    def _test_stopping_service(server_service_name, target_service_name) -> None:
        SigtermHandling.await_net_io_stop(server_service_name)
        docker.stop([target_service_name])
        zero_exit_code_count = docker.await_containers([target_service_name])
        if zero_exit_code_count != 1:
            raise ValueError(f"{target_service_name} exited with an error code")

    @staticmethod
    def test() -> None:
        docker_compose_content = docker_compose.read(DOCKER_COMPOSE_PATH)
        services = docker_compose_content["services"]

        client_service_name = docker_compose.find_services_by_context(
            services, "client"
        )[0]
        server_service_name = docker_compose.find_services_by_context(
            services, "server"
        )[0]
        SigtermHandling.with_docker_run(
            DOCKER_COMPOSE_PATH,
            lambda: SigtermHandling._test_stopping_service(
                server_service_name, client_service_name
            ),
        )
        SigtermHandling.with_docker_run(
            DOCKER_COMPOSE_PATH,
            lambda: SigtermHandling._test_stopping_service(
                server_service_name, server_service_name
            ),
        )
