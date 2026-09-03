import socket
import logger
import safe_socket
import os

# from services.server.src_frozen.lottery.bet import Bet
# from services.server.src_frozen.lottery.lottery import Lottery
#
from lottery import Lottery, Bet

_ECHO_SERVER_MESSAGE_SIZE = 1024
_CLIENT_END_MSG = "END"
_CLIENT_ACK_MSG = "OK"
STORAGE_PATH = os.getenv("STORAGE_PATH")


class Server:
    def __init__(self, server_host: str, server_port: int) -> None:
        self.server_host = server_host
        self.server_port = server_port

        self.lottery = Lottery(STORAGE_PATH)

    def _handle_client(self, client_socket):
        action = "handle-client"
        message_amount = 0
        try:
            logger.info(action, logger.LogResult.in_progress)
            bets = []
            while True:
                client_message: bytes = client_socket.recv(_ECHO_SERVER_MESSAGE_SIZE)
                if not client_message:
                    logger.info(
                        action,
                        logger.LogResult.success,
                        "messages-amount",
                        message_amount,
                    )
                    return

                client_message_str = client_message.decode()
                if client_message_str == _CLIENT_END_MSG:
                    break

                csv_fields: list[str] = client_message_str.split(",")
                print(client_message_str)
                bet = Bet(
                    int(csv_fields[0]),
                    csv_fields[1],
                    csv_fields[2],
                    int(csv_fields[3]),
                    csv_fields[4],
                    int(csv_fields[5]),
                )
                bets.append(bet)

                message_amount += 1
                safe_socket.send_all(client_socket, _CLIENT_ACK_MSG.encode())

            self.lottery.store_bets(bets)
            self.lottery.load_bets()
            winners = filter(lambda bet: self.lottery.has_won(bet), bets)
            for bet in winners:
                row = f"{bet.first_name},{bet.last_name},{bet.document},{bet.birthdate},{bet.number}\n"
                safe_socket.send_all(client_socket, row.encode())
            safe_socket.send_all(client_socket, b"END\n")

        except Exception as e:
            logger.error(
                action, logger.LogResult.fail, "messages-amount", message_amount
            )
            raise e
        finally:
            client_socket.close()

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
