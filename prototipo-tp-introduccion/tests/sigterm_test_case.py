import time
import multiprocessing

from .utils import docker, docker_compose
from .test_case import TestCase

SECONDS_BEFORE_SIGTERM = 5


def _stop_service(client_service) -> None:
    time.sleep(SECONDS_BEFORE_SIGTERM)
    docker.stop([client_service])


class SigtermHandling(TestCase):
    name = "sigterm-handling"

    def _test_stopping_service(self, log, service_name) -> None:
        log(f"Sending SIGTERM to {service_name}")
        stop_service_process = None
        try:
            stop_service_process = multiprocessing.Process(
                target=_stop_service, args=(service_name,)
            )
            stop_service_process.start()
            docker.up()
            zero_exit_code_count = docker.await_containers([service_name])
            if zero_exit_code_count != 1:
                raise ValueError(f"{service_name} exited with an error code")
        finally:
            if stop_service_process:
                stop_service_process.join()
            docker.down()

    def test(self, log, docker_compose_path) -> None:
        services = docker_compose.read_services(docker_compose_path)

        client_service = docker_compose.find_services_by_context(services, "client")[0]
        self._test_stopping_service(log, client_service)

        server_service = docker_compose.find_services_by_context(services, "server")[0]
        self._test_stopping_service(log, server_service)
