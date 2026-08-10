from .test_case import TestCase
from utils import shell_cmd

GOLANG_FILES_PATH = "./services/client"
PYTHON_FILES_PATH = "./services/server"


class ForcedExit(TestCase):
    title = "forced exit"
    error_hint = "exit syscall must not be used to force an abrupt ending without freeing resources, it's only allowed to specify the return code"

    @staticmethod
    def _test_python_os_sys_exit_use() -> None:
        files = shell_cmd.search_files_containing(
            PYTHON_FILES_PATH, "sys.exit\\([^)]*\\)"
        )
        files += shell_cmd.search_files_containing(
            PYTHON_FILES_PATH, "os._exit\\([^)]*\\)"
        )
        if len(files) == 0:
            return
        if len(set(files)) > 1 or not "main.py" in files[0]:
            raise LookupError("os/sys exit call found outside server entrypoint file")

    @staticmethod
    def _test_python_quit_exit_use() -> None:
        files = shell_cmd.search_files_containing(
            PYTHON_FILES_PATH, "\\squit\\([^)]*\\)"
        )
        files += shell_cmd.search_files_containing(
            PYTHON_FILES_PATH, "\\sexit\\([^)]*\\)"
        )
        if len(files) > 0:
            raise LookupError(
                "shell oriented exit or quit functions found, use os/sys exit instead"
            )

    @staticmethod
    def _test_python_system_exit_use() -> None:
        files = shell_cmd.search_files_containing(PYTHON_FILES_PATH, "SystemExit")
        if len(files) > 0:
            raise LookupError("direct SystemExit raise found, use os/sys exit instead")

    @staticmethod
    def _test_golang_os_exit_use() -> None:
        files = shell_cmd.search_files_containing(GOLANG_FILES_PATH, "os.Exit")
        if len(files) == 0:
            return
        if len(set(files)) > 1 or not "main.go" in files[0]:
            raise LookupError("os.Exit call found outside client entrypoint file")

    @staticmethod
    def test() -> None:
        ForcedExit._test_python_os_sys_exit_use()
        ForcedExit._test_python_quit_exit_use()
        ForcedExit._test_python_system_exit_use()
        ForcedExit._test_golang_os_exit_use()
