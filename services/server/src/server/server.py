import os
import socket
import logger
import protocol
from lottery import Lottery, Bet


class Server:
    def __init__(self, server_host: str, server_port: int, storage_path: str = "bets.csv") -> None:
        self.server_host = server_host
        self.server_port = server_port
        self.storage_path = storage_path
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)
        self.lottery = Lottery(self.storage_path)

    def _handle_client(self, client_socket):
        action = "handle-client"
        message_amount = 0
        try:
            logger.info(action, logger.LogResult.in_progress)
            while True:
                msg_type, payload = protocol.recv_msg(client_socket)
                if msg_type is None:
                    logger.info(
                        action,
                        logger.LogResult.success,
                        "messages-amount",
                        message_amount,
                    )
                    return

                if msg_type == protocol.MSG_BET:
                    text = payload.decode("utf-8")
                    bets = []
                    for line in text.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split(",")
                        agency_id = int(parts[0])
                        first_name = parts[1]
                        last_name = parts[2]
                        document = int(parts[3])
                        birthdate = parts[4]
                        number = int(parts[5])
                        bets.append(
                            Bet(
                                agency_id,
                                first_name,
                                last_name,
                                document,
                                birthdate,
                                number,
                            )
                        )
                    if bets:
                        self.lottery.store_bets(bets)
                        message_amount += len(bets)
                    protocol.send_msg(client_socket, protocol.MSG_ACK)

                elif msg_type == protocol.MSG_END_BETS:
                    agency_id = int(payload.decode("utf-8").strip())
                    winners = [
                        bet
                        for bet in self.lottery.load_bets()
                        if bet.agency_id == agency_id and self.lottery.has_won(bet)
                    ]
                    winner_lines = [
                        f"{bet.first_name},{bet.last_name},{bet.document},{bet.birthdate},{bet.number}"
                        for bet in winners
                    ]
                    response_payload = "\n".join(winner_lines).encode("utf-8")
                    if response_payload:
                        response_payload += b"\n"
                    protocol.send_msg(
                        client_socket, protocol.MSG_WINNERS, response_payload
                    )
                else:
                    logger.warn("unknown-msg-type", logger.LogResult.fail, "type", msg_type)

        except Exception as e:
            logger.error(
                action, logger.LogResult.fail, "messages-amount", message_amount, "err", e
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
