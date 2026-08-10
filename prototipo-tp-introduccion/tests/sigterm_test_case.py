import multiprocessing

from .utils import docker, docker_compose
from .test_case import TestCase

DOCKER_COMPOSE_PATH = "docker-compose-no-agency-quorum.yaml"


def _await_target_service(target_service_name, pipe_send) -> None:
    zero_exit_code_count = docker.await_containers([target_service_name])
    pipe_send.send(zero_exit_code_count)


class SigtermHandling(TestCase):
    title = "sigterm handling"
    error_hint = "The SIGTERM signal must be correctly handled as soon as possible and at any stage of the communication in both the clients and the server"

    @staticmethod
    def _test_stopping_service(server_service_name, target_service_name) -> None:
        SigtermHandling.await_net_io_stop(server_service_name)
        pipe_recv, pipe_send = multiprocessing.Pipe()
        stop_service_process = None
        try:
            stop_service_process = multiprocessing.Process(
                target=_await_target_service, args=(target_service_name, pipe_send)
            )
            stop_service_process.start()
            docker.stop([target_service_name])
            zero_exit_code_count = pipe_recv.recv()
            if zero_exit_code_count != 1:
                raise ValueError(f"{target_service_name} exited with an error code")
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
