import socket
import logger
import safe_socket
import threading
import queue
from protocol.message_type import MessageType
from protocol.unpacker import unpack_bets
from protocol.packer import generate_winning_bets_packet
from coordinator.coordinator import start_coordinator

class Server:
    def __init__(self, server_host: str, server_port: int, storage_dir: str, agency_quorum_min: int) -> None:
        self.server_host = server_host
        self.server_port = server_port
        self.coordinator_queue = queue.Queue()
        self.storage_dir = storage_dir
        self.agency_quorum_min = agency_quorum_min

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
        self.coordinator_queue.put(("STORE_BETS" , bets))
        logger.info("read_bet_message", logger.LogResult.success, "bets-received", f"Received {len(bets)} bets from agency {agency_id}")
        return True

    def _read_all_bets_sent_message(self,socket,reading_queue) -> bool:
        logger.info("read_all_bets_sent_message", logger.LogResult.success, "all-bets-sent", "All bets have been sent")
        agency_id_bytes = safe_socket.recv_all(socket, 1)
        agency_id = int.from_bytes(agency_id_bytes, byteorder='big')
        self.coordinator_queue.put(("AGENCY_SENT_ALL_BETS", (agency_id, reading_queue)))
        winning_bets = reading_queue.get()
        logger.info("read_all_bets_sent_message", logger.LogResult.success, "winning-bets", f"Found {len(winning_bets)} winning bets for agency {agency_id}")
        winning_bets_packet = generate_winning_bets_packet(winning_bets)
        safe_socket.send_all(socket, winning_bets_packet)
        return True

    def _read_message(self,socket,reading_queue):
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
            return self._read_all_bets_sent_message(socket, reading_queue)



    def _handle_client(self, client_socket):
        action = "handle-client"
        reading_queue = queue.Queue()
        message_amount = 0
        try:
            logger.info(action, logger.LogResult.in_progress,"process id", f"Handling client with process id {threading.get_ident()}")
            while True:
                client_message = self._read_message(client_socket,reading_queue)
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

        coordinator = threading.Thread(target=start_coordinator, args=(self.agency_quorum_min, self.storage_dir, self.coordinator_queue), daemon=True)
        coordinator.start()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.server_host, self.server_port))
            server_socket.listen()
            while True:
                try:
                    logger.info(action, logger.LogResult.in_progress)
                    client_socket, _ = server_socket.accept()
                    client_thread = threading.Thread(target=self._handle_client, args=(client_socket,))
                    client_thread.start()
                except Exception as e:
                    logger.error(action, logger.LogResult.fail)
                    raise e
                logger.info(action, logger.LogResult.success)

