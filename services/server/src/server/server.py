import socket
import logger
import safe_socket
from protocol.message_handler import read_message
from protocol.bet import bet_from_bytes
from lottery.lottery import Lottery

class Server:
    def __init__(self, server_host: str, server_port: int, storage_dir: str) -> None:
        self.server_host = server_host
        self.server_port = server_port
        self.lottery = Lottery(storage_dir)

    def _handle_client(self, client_socket):
        action = "handle-client"
        message_amount = 0
        bet_list = []
        try:
            logger.info(action, logger.LogResult.in_progress)
            while True:
                client_message = read_message(client_socket)
                if not client_message:
                    logger.info(
                        action,
                        logger.LogResult.success,
                        "messages-amount",
                        message_amount,
                    )
                    self.lottery.store_bets(bet_list)
                    return
                bet = bet_from_bytes(client_message)
                logger.info(
                    action,
                    logger.LogResult.success,
                    "bet",
                    {
                        "agency_id": bet.agency_id,
                        "first_name": bet.first_name,
                        "last_name": bet.last_name,
                        "document": bet.document,
                        "birthdate": bet.birthdate,
                        "number": bet.number,
                    },
                )
                bet_list.append(bet)
                message_amount += 1
                safe_socket.send_all(client_socket, client_message)
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
