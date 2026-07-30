import subprocess


def run(
    cmd: list[str],
    cwd: str | None = None,
    capture: bool = False,
    check: bool = False,
    shell: bool = False,
    env: dict | None = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
        stderr=subprocess.PIPE if capture else subprocess.DEVNULL,
        check=check,
        shell=shell,
        env=env,
    )
