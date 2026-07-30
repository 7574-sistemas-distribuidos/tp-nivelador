import time

from .utils import docker, docker_compose
from .test_case import TestCase

SECONDS_BEFORE_CONCURRENCY_CHECK = 5


class Concurrency(TestCase):
    name = "concurrency"

    def test(self, log, docker_compose_path) -> None:
        docker_compose_content = docker_compose.read(docker_compose_path)
        services = docker_compose_content["services"]
        server_service_name = docker_compose.find_services_by_context(
            services, "server"
        )[0]

        agency_quorum_min = docker_compose.find_environment_variable(
            services[server_service_name], "AGENCY_QUORUM_MIN"
        )
        docker_compose.add_environment_variable(
            services[server_service_name],
            "AGENCY_QUORUM_MIN",
            int(agency_quorum_min) + 1,
        )
        docker_compose.write(docker_compose_path, docker_compose_content)

        try:
            docker.up()
            time.sleep(SECONDS_BEFORE_CONCURRENCY_CHECK)
            server_pids = docker.get_container_pids(server_service_name)
            if server_pids < 2:
                raise ValueError(
                    f"{server_service_name} runs on a single thread/process"
                )
        finally:
            docker.down()
            docker_compose.add_environment_variable(
                services[server_service_name], "AGENCY_QUORUM_MIN", agency_quorum_min
            )
            docker_compose.write(docker_compose_path, docker_compose_content)
