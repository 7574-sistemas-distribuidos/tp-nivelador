import io
import os
import subprocess

PIPE = subprocess.PIPE


def run(
    cmd: list[str],
    cwd: str | None = None,
    redirect_output: io.TextIOWrapper | int | None = subprocess.DEVNULL,
    check: bool = False,
    shell: bool = False,
    env: dict[str, str] = {},
) -> subprocess.CompletedProcess:

    return subprocess.run(
        cmd,
        cwd=cwd,
        stdout=redirect_output,
        stderr=redirect_output,
        check=check,
        shell=shell,
        env=os.environ | env,
    )


def search_files_containing(base_path: str, lookup_string: str) -> list[str]:
    result = run(["grep", "-lir", "-i", lookup_string, base_path], redirect_output=PIPE)
    output = result.stdout.decode("utf-8").rstrip("\n")
    if len(output) > 0:
        return output.split("\n")
    return []
