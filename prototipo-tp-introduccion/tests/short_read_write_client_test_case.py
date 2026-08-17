from .utils import docker, docker_compose
from .test_case import TestCase

DOCKER_COMPOSE_PATH = "docker-compose-client-short-read-write-tester.yaml"


class ClientShortReadWrite(TestCase):
    title = "client short read/write"
    error_hint = "I/O doesn't guarantee a full read/write in a single call"

    @staticmethod
    def _test() -> None:
        golang_short_read_write_tester = "golang_short_read_write_tester"
        zero_exit_code_count = docker.await_containers([golang_short_read_write_tester])
        if zero_exit_code_count != 1:
            raise ValueError(f"The client short read write tests failed")

    @staticmethod
    def test() -> None:
        ClientShortReadWrite.with_docker_run(
            DOCKER_COMPOSE_PATH, ClientShortReadWrite._test
        )
