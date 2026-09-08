from .test_case import TestCase
from utils import shell_cmd

GOLANG_FILES_PATH = "./services/client"
PYTHON_FILES_PATH = "./services/server"


class Json(TestCase):
    title = "json import"
    error_hint = "Json import is forbidden for this practical task"
    has_service_logs = False

    @staticmethod
    def test() -> None:
        server_files = shell_cmd.search_files_containing(
            PYTHON_FILES_PATH, "import json"
        )
        if len(server_files) > 0:
            raise LookupError(f"json is imported in the server")

        client_files = shell_cmd.search_files_containing(
            GOLANG_FILES_PATH, "encoding/json"
        )
        if len(client_files) > 0:
            raise LookupError(f"json is imported in the client")
