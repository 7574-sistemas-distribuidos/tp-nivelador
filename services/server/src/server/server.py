import socket
import logger
import safe_socket
from protocol.bet import bet_from_bytes
from protocol.message_receiver import handle_message
from lottery.lottery import Lottery

class Server:
    def __init__(self, server_host: str, server_port: int, storage_dir: str) -> None:
        self.server_host = server_host
        self.server_port = server_port
        self.lottery = Lottery(storage_dir)

    def _handle_client(self, client_socket):
        action = "handle-client"
        message_amount = 0
        try:
            logger.info(action, logger.LogResult.in_progress)
            while True:
                client_message = handle_message(client_socket,self.lottery)
                if not client_message:
                    logger.info(
                        action,
                        logger.LogResult.success,
                        "messages-amount",
                        message_amount,
                    )
                    return
                message_amount += 1
                safe_socket.send_all(client_socket, b'\x01')
        except Exception as e:
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
