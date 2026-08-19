from .utils import docker
from .test_case import TestCase

DOCKER_COMPOSE_PATH = (
    "./tests/compose_files/docker-compose-client-short-read-write-tester.yaml"
)


class ClientShortReadWrite(TestCase):
    title = "client short read/write"
    error_hint = "I/O doesn't guarantee a full read/write in a single call"

    @staticmethod
    def _test() -> None:
        client_short_read_write_tester = "client_short_read_write_tester"
        zero_exit_code_count = docker.await_containers([client_short_read_write_tester])
        if zero_exit_code_count != 1:
            raise ValueError(f"The client short read write tests failed")

    @staticmethod
    def test() -> None:
        ClientShortReadWrite.with_docker_run(
            DOCKER_COMPOSE_PATH, ClientShortReadWrite._test
        )
