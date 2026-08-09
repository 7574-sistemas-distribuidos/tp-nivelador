from .utils import docker


class TestCase:
    name: str = ""
    error_hint: str = ""

    @staticmethod
    def with_docker_run(docker_compose_path: str, test_callback) -> None:
        try:
            docker.up(docker_compose_path)
            test_callback()
        finally:
            docker.down(docker_compose_path)

    @staticmethod
    def test() -> None:
        raise NotImplementedError("Test cases require a test function")
