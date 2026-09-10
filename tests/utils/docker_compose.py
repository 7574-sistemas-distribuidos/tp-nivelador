import yaml
from . import shell_cmd


def read(docker_compose_path):
    with open(docker_compose_path) as docker_compose_file:
        docker_compose_parsed = yaml.safe_load(docker_compose_file)
    return docker_compose_parsed


def find_services_by_context(services, context_name):
    return [
        service
        for service in services
        if context_name in services[service]["build"]["context"]
    ]


def find_environment_variable(service, target_environment_variable) -> str:
    environment_variables = service["environment"]
    for environment_variable in environment_variables:
        [name, value] = environment_variable.split("=")
        if name == target_environment_variable:
            return value

    raise LookupError(f"Environment variable not found {target_environment_variable}")


def dump_logs(docker_compose_path: str, dump_file):
    shell_cmd.run(
        ["docker", "compose", "-f", docker_compose_path, "logs"],
        redirect_output=dump_file,
    )


def get_container_last_logs(docker_compose_path: str, service_name: str, tail=10):
    result = shell_cmd.run(
        [
            "docker",
            "compose",
            "-f",
            docker_compose_path,
            "logs",
            service_name,
            "--tail",
            str(tail),
        ],
        redirect_output=shell_cmd.PIPE,
    )
    return result.stdout.decode("utf-8")
