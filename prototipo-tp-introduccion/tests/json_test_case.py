from .test_case import TestCase
from utils import shell_cmd


class Json(TestCase):
    title = "json import"

    @staticmethod
    def test() -> None:
        server_files = shell_cmd.search_files_containing(
            "./services/server", "import json"
        )
        if len(server_files) > 0:
            raise LookupError(f"json is imported in the server")
        client_files = shell_cmd.search_files_containing(
            "./services/client", "encoding/json"
        )
        if len(client_files) > 0:
            raise LookupError(f"json is imported in the client")
