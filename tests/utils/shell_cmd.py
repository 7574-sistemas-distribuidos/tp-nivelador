import os
import subprocess


def run(
    cmd: list[str],
    cwd: str | None = None,
    capture: bool = False,
    check: bool = False,
    shell: bool = False,
    env: dict[str, str] = {},
) -> subprocess.CompletedProcess:

    return subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
        stderr=subprocess.PIPE if capture else subprocess.DEVNULL,
        check=check,
        shell=shell,
        env=os.environ | env,
    )


def search_files_containing(base_path: str, lookup_string: str) -> list[str]:
    result = run(["grep", "-lir", "-i", lookup_string, base_path], capture=True)
    output = result.stdout.decode("utf-8").rstrip("\n")
    if len(output) > 0:
        return output.split("\n")
    return []
