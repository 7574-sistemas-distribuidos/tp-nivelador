from abc import ABC


class TestCase(ABC):
    name: str

    def test(self, log, docker_compose_path) -> None:
        pass
