import json
from .test_case import TestCase
from utils import shell_cmd


class Json(TestCase):
    name = "json"

    def test(self, log, docker_compose_path) -> None:
        server_files = shell_cmd.search_files_containing("./services/server", "import json")
        if len(server_files) > 0:
            raise LookupError(f"json is imported in the server")
        client_files = shell_cmd.search_files_containing("./services/clint", "encoding/json")
        if len(client_files) > 0:
            raise LookupError(f"json is imported in the client")

