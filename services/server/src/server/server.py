import socket
import logger
import safe_socket
from protocol.bet import bet_from_bytes
from lottery.lottery import Lottery
from protocol.message_type import MessageType
from protocol.unpacker import unpack_bets
from protocol.packer import generate_winning_bets_packet

class Server:
    def __init__(self, server_host: str, server_port: int, storage_dir: str) -> None:
        self.server_host = server_host
        self.server_port = server_port
        self.lottery = Lottery(storage_dir)

    def _read_bet_message(self,socket) -> bool:
        agency_id_bytes = safe_socket.recv_all(socket, 1)
        agency_id = int.from_bytes(agency_id_bytes)
        logger.info("read_bet_message", logger.LogResult.in_progress, "bets-receiving", f"Receiving bets from agency {agency_id}")
        bets_amount_bytes = safe_socket.recv_all(socket,4)
        bets_amount = int.from_bytes(bets_amount_bytes, byteorder='big')
        logger.info("read_bet_message", logger.LogResult.in_progress, "bets-receiving", f"Receiving {bets_amount} bets from agency {agency_id}")
        payload_length_bytes = safe_socket.recv_all(socket,4)
        payload_length = int.from_bytes(payload_length_bytes, byteorder='big')
        logger.info("read_bet_message", logger.LogResult.in_progress, "bets-receiving", f"Receiving payload of length {payload_length} from agency {agency_id}")
        payload = safe_socket.recv_all(socket,payload_length)
        bets = unpack_bets(payload,bets_amount,agency_id)
        self.lottery.store_bets(bets)
        logger.info("read_bet_message", logger.LogResult.success, "bets-received", f"Received {len(bets)} bets from agency {agency_id}")
        return True

    def _read_all_bets_sent_message(self,socket) -> bool:
        logger.info("read_all_bets_sent_message", logger.LogResult.success, "all-bets-sent", "All bets have been sent")
        agency_id_bytes = safe_socket.recv_all(socket, 1)
        agency_id = int.from_bytes(agency_id_bytes, byteorder='big')
        winning_bets = []
        bets = self.lottery.load_bets()
        for bet in bets:
            if self.lottery.has_won(bet) and bet.agency_id == agency_id:
                winning_bets.append(bet)
        logger.info("read_all_bets_sent_message", logger.LogResult.success, "winning-bets", f"Found {len(winning_bets)} winning bets for agency {agency_id}")
        winning_bets_packet = generate_winning_bets_packet(winning_bets)
        safe_socket.send_all(socket, winning_bets_packet)
        return True

    def _read_message(self,socket):
        logger.info("lottery", logger.LogResult.in_progress, "message-receiving", "Receiving message")
        message_type_bytes = safe_socket.recv_all(socket, 1)
        if not message_type_bytes:
            logger.info("lottery", logger.LogResult.success, "message-receiving", "No more messages to receive")
            return None
        message_type = MessageType(int.from_bytes(message_type_bytes))
        
        if message_type == MessageType.BET:
            logger.info("lottery", logger.LogResult.in_progress, "bet-received", "Receiving bet message")
            return self._read_bet_message(socket)
        
        if message_type == MessageType.ALL_BETS_SENT:
            logger.info("lottery", logger.LogResult.success, "all-bets-sent", "All bets have been sent")
            return self._read_all_bets_sent_message(socket)



    def _handle_client(self, client_socket):
        action = "handle-client"
        message_amount = 0
        try:
            logger.info(action, logger.LogResult.in_progress)
            while True:
                client_message = self._read_message(client_socket)
                if not client_message:
                    logger.info(
                        action,
                        logger.LogResult.success,
                        "messages-amount",
                        message_amount,
                    )
                    return
                message_amount += 1
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
