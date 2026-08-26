import csv
import os
from pathlib import Path
import socket
import logger
import safe_socket

_ECHO_SERVER_MESSAGE_SIZE = 1024
OUTPUT_FILE = os.getenv("OUTPUT_FILE")


class Server:
    def __init__(self, server_host: str, server_port: int) -> None:
        self.server_host = server_host
        self.server_port = server_port

    def _handle_client(self, client_socket):
        action = "handle-client"
        message_amount = 0
        csv_writer = None

        if OUTPUT_FILE:
            path = Path(OUTPUT_FILE)
        else:
            logger.error("write-file", logger.LogResult.fail)

        try:
            logger.info(action, logger.LogResult.in_progress)
            while True:
                client_message = safe_socket.recv_all(
                    client_socket, _ECHO_SERVER_MESSAGE_SIZE
                )
                if not client_message:
                    logger.info(
                        action,
                        logger.LogResult.success,
                        "messages-amount",
                        message_amount,
                    )
                    return
                with open(path, "a") as file:
                    csv_writer = csv.writer(file)

                    client_message_str = client_message.decode()
                    row_data = client_message_str.split(",")

                    message_amount += 1
                    csv_writer.writerow(row_data)

                safe_socket.send_all(client_socket, client_message)
        except Exception as e:
            print(e)
            logger.error(
                action, logger.LogResult.fail, "messages-amount", message_amount
            )
            raise e

    def run(self):
        action = "accept-connection"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.server_host, self.server_port))
            server_socket.listen()
            while True:
                try:
                    logger.info(action, logger.LogResult.in_progress)
                    client_socket, _ = server_socket.accept()
                except Exception as e:
                    logger.error(action, logger.LogResult.fail)
                    raise e
                logger.info(action, logger.LogResult.success)

                self._handle_client(client_socket)
