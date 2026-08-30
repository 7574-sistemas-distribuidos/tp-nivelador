import json

from . import shell_cmd


def up(docker_compose_path: str | None):
    args = ["make", "up"]
    env = {}
    if docker_compose_path:
        env["DOCKER_FILE_PATH"] = docker_compose_path
    shell_cmd.run(args, env=env)


def down(docker_compose_path: str | None):
    args = ["make", "down"]
    env = {}
    if docker_compose_path:
        env["DOCKER_FILE_PATH"] = docker_compose_path
    shell_cmd.run(args, env=env)


def stop(service_names: list[str], grace_period_seconds=5):
    shell_cmd.run(["docker", "stop", "-t", str(grace_period_seconds), *service_names])


def await_containers(service_names: list[str]) -> int:
    result = shell_cmd.run(
        ["docker", "container", "wait", *service_names], redirect_output=shell_cmd.PIPE
    )
    zero_exit_code_count = 0
    for char in result.stdout.decode("utf-8"):
        if char == "0":
            zero_exit_code_count += 1

    return zero_exit_code_count


def _get_file_contents(service_name: str, filepath: str) -> str:
    result = shell_cmd.run(
        ["docker", "exec", service_name, "sh", "-c", f"cat {filepath}"],
        redirect_output=shell_cmd.PIPE,
    )
    return result.stdout


def get_container_peak_memory_in_bytes(service_name: str) -> int:
    return int(_get_file_contents(service_name, filepath="/sys/fs/cgroup/memory.peak"))


def _get_container_stats(service_name: str):
    result = shell_cmd.run(
        [
            "docker",
            "stats",
            "--format",
            "json",
            "--no-stream",
            "--no-trunc",
            service_name,
        ],
        redirect_output=shell_cmd.PIPE,
    )
    return json.loads(result.stdout.decode("utf-8"))


def get_container_pids(service_name: str):
    output = _get_container_stats(service_name)
    return int(output["PIDs"])


def get_container_net_io(service_name: str):
    output = _get_container_stats(service_name)
    [net_recv, net_sent] = output["NetIO"].split("/")
    return net_recv.strip(), net_sent.strip()
