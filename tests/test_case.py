import time
from .utils import docker


class TestCase:
    name: str = ""
    error_hint: str = ""

    @staticmethod
    def with_docker_run(docker_compose_path: str, test_callback):
        try:
            docker.up(docker_compose_path)
            result = test_callback()
            docker.down(docker_compose_path)
            return result
        except Exception as e:
            docker.down(docker_compose_path)
            raise e

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
