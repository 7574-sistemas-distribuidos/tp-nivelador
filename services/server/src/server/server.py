import socket
import logger
import safe_socket
import threading
import queue
import signal
from protocol.message_type import MessageType
from protocol.unpacker import unpack_bets
from protocol.packer import generate_winning_bets_packet
from coordinator.coordinator import Coordinator

class Server:
    def __init__(self, server_host: str, server_port: int, storage_dir: str, agency_quorum_min: int) -> None:
        self.server_host = server_host
        self.server_port = server_port
        self.coordinator_queue = queue.Queue()
        self.storage_dir = storage_dir
        self.shutdown_event = threading.Event()
        self.active_threads = []
        self.client_sockets = set()
        self.lock = threading.Lock()
        self.agency_quorum_min = agency_quorum_min
        self.coordinator = Coordinator(agency_quorum_min, storage_dir, self.coordinator_queue)


    def _setup_signals(self):
        def _handle_sigterm(signum, frame):
            logger.info("server", logger.LogResult.in_progress, "sigterm", "SIGTERM received, initiating graceful shutdown")
            self.shutdown_event.set()

        signal.signal(signal.SIGTERM, _handle_sigterm)
        signal.signal(signal.SIGINT, _handle_sigterm)

    def _read_bet_message(self,socket) -> bool:
        agency_id_bytes = safe_socket.recv_all(socket, 1)
        agency_id = int.from_bytes(agency_id_bytes)
        
        bets_amount_bytes = safe_socket.recv_all(socket,4)
        bets_amount = int.from_bytes(bets_amount_bytes, byteorder='big')
        
        payload_length_bytes = safe_socket.recv_all(socket,4)
        payload_length = int.from_bytes(payload_length_bytes, byteorder='big')
        
        payload = safe_socket.recv_all(socket,payload_length)
        bets = unpack_bets(payload,bets_amount,agency_id)
        self.coordinator_queue.put(("STORE_BETS" , bets))
        safe_socket.send_all(socket, bytearray([MessageType.ACK_BET]))
        return True

    def _read_all_bets_sent_message(self,socket,reading_queue) -> bool:
        logger.info("read_all_bets_sent_message", logger.LogResult.success, "all-bets-sent", "All bets have been sent")
        agency_id_bytes = safe_socket.recv_all(socket, 1)
        agency_id = int.from_bytes(agency_id_bytes, byteorder='big')
        self.coordinator_queue.put(("AGENCY_SENT_ALL_BETS", (agency_id, reading_queue)))
        (msg, payload) = reading_queue.get()
        if msg == "SHUTDOWN":
            return False
        winning_bets = payload
        logger.info("read_all_bets_sent_message", logger.LogResult.success, "winning-bets", f"Found {len(winning_bets)} winning bets for agency {agency_id}")
        winning_bets_packet = generate_winning_bets_packet(winning_bets)
        safe_socket.send_all(socket, winning_bets_packet)
        return True

    def _read_message(self,socket,reading_queue):
        message_type_bytes = safe_socket.recv_all(socket, 1)
        if not message_type_bytes:
            logger.info("lottery", logger.LogResult.success, "message-receiving", "No more messages to receive")
            return None
        message_type = MessageType(int.from_bytes(message_type_bytes))
        
        if message_type == MessageType.BET:
            return self._read_bet_message(socket)
        
        if message_type == MessageType.ALL_BETS_SENT:
            logger.info("lottery", logger.LogResult.success, "all-bets-sent", "All bets have been sent")
            return self._read_all_bets_sent_message(socket, reading_queue)



    def _handle_client(self, client_socket):
        reading_queue = queue.Queue()
        with self.lock:
            self.client_sockets.add(client_socket)
        try:
            while not self.shutdown_event.is_set():
                client_message = self._read_message(client_socket, reading_queue)
                if not client_message:
                    break
        except Exception as e:
            logger.error("handle-client", logger.LogResult.fail, "error", str(e))
        finally:
            with self.lock:
                self.client_sockets.discard(client_socket)
            try:
                client_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            client_socket.close()

    def run(self):
        self._setup_signals()
        coord_thread = threading.Thread(target=self.coordinator.start, daemon=False)
        coord_thread.start()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.server_host, self.server_port))
            server_socket.listen()
            server_socket.settimeout(0.5)

            while not self.shutdown_event.is_set():
                try:
                    client_socket, _ = server_socket.accept()
                    t = threading.Thread(target=self._handle_client, args=(client_socket,))
                    t.start()
                    with self.lock:
                        self.active_threads.append(t)
                except socket.timeout:
                    continue
                except OSError:
                    break

        logger.info("server", logger.LogResult.in_progress, "shutdown", "Closing active client connections")
        with self.lock:
            for s in list(self.client_sockets):
                try:
                    s.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                s.close()

        for t in self.active_threads:
            t.join(timeout=1.0)

        self.coordinator.stop()
        coord_thread.join(timeout=1.0)
        logger.info("server", logger.LogResult.success, "shutdown", "Server stopped cleanly")

