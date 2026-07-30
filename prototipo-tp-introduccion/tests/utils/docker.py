from . import shell_cmd


def up():
    shell_cmd.run(["make", "up"], capture=False)


def down():
    shell_cmd.run(["make", "down"], capture=False)


def stop(service_names: list[str], grace_period_seconds=10):
    shell_cmd.run(
        ["docker", "stop", "-t", str(grace_period_seconds), *service_names],
        capture=False,
    )


def await_containers(service_names: list[str]) -> int:
    result = shell_cmd.run(
        ["docker", "container", "wait", *service_names], capture=True
    )
    zero_exit_code_count = 0
    for char in result.stdout.decode("utf-8"):
        if char == "0":
            zero_exit_code_count += 1

    return zero_exit_code_count
