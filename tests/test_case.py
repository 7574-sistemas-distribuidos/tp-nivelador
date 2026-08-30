import time
from typing import Callable

from utils import docker, docker_compose

LOGS_DUMP_FILE_PATH = "failed_test.log"


class TestCase:
    title: str = ""
    error_hint: str = ""

    @staticmethod
    def with_docker_run(
        docker_compose_path: str,
        test_callback: Callable,
    ):
        try:
            docker.up(docker_compose_path)
            result = test_callback()
            docker.down(docker_compose_path)
            return result
        except:
            with open(LOGS_DUMP_FILE_PATH, "w") as dump_file:
                docker_compose.dump_logs(docker_compose_path, dump_file)
            docker.down(docker_compose_path)
            raise

    @staticmethod
    def await_net_io_stop(service_name: str, pooling_await_seconds=1):
        last_net_recv = ""
        last_net_sent = ""
        while True:
            [net_recv, net_sent] = docker.get_container_net_io(service_name)
            if last_net_recv == net_recv and last_net_sent == net_sent:
                return
            last_net_recv = net_recv
            last_net_sent = net_sent
            time.sleep(pooling_await_seconds)

    @staticmethod
    def test() -> None:
        raise NotImplementedError("Test cases require a test function")
