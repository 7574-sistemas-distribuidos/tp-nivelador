import os
import socket
import threading
import logger
import lottery
from protocol import (PacketType, receive_from, send_response, send_ack,
                      send_eof, deserialize_batch)

BETS_FILE = "bets.csv"
INIT_SEQ_NUM = 0


class Server:
    def __init__(self, server_host: str, server_port: int) -> None:
        self.server_host = server_host
        self.server_port = server_port
        open(BETS_FILE, 'w').close()
        self.lottery = lottery.Lottery(BETS_FILE)

        self.quorum = int(os.getenv("AGENCY_QUORUM_MIN", "1"))
        self.lock = threading.Lock()
        self.winners = None

        self.barrier = threading.Barrier(self.quorum, action=self._calculate_winners)

   
        self.shutdown_event = threading.Event()
        self.server_socket = None
        self.active_clients = []          
        self.active_clients_lock = threading.Lock()

    def shutdown(self):
        logger.info("shutdown", logger.LogResult.in_progress)
        self.shutdown_event.set()

        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except OSError:
                pass

        with self.active_clients_lock:
            clients_snapshot = list(self.active_clients)
        for client_socket, _ in clients_snapshot:
            try:
                client_socket.close()
            except OSError:
                pass

        try:
            self.barrier.abort()
        except Exception:
            pass

    def _handle_client(self, client_socket):
        action = "handle-client"
        seq_num = INIT_SEQ_NUM
        try:
            logger.info(action, logger.LogResult.in_progress)

            agency_id, seq_num = self._receive_init(client_socket)
            logger.info(action, logger.LogResult.in_progress, "agency_id", agency_id)

            while True:
                if self.shutdown_event.is_set():
                    logger.info(action, "shutdown-detected")
                    return
                packet = receive_from(client_socket)
                if packet.type() == PacketType.REQUEST.value:
                    seq_num = self._receive_bets(client_socket, packet, seq_num)
                elif packet.type() == PacketType.EOF.value:
                    send_ack(client_socket, packet.sequence_number(), b'OK')
                    logger.info(action, logger.LogResult.in_progress, "eof-received")
                    seq_num = packet.sequence_number() + 1
                    break

            if self.shutdown_event.is_set():
                return
            try:
                self.barrier.wait()
            except threading.BrokenBarrierError:
                logger.info(action, "barrier-aborted")
                return

            if self.shutdown_event.is_set():
                return

            with self.lock:
                winners = self.winners

            seq_num = self._send_winners(client_socket, seq_num, agency_id, winners)

            send_eof(client_socket, seq_num)
            ack = receive_from(client_socket)
            if ack.type() != PacketType.ACK.value or ack.sequence_number() != seq_num:
                logger.error("final-ack-mismatch", "expected", seq_num, "received", ack.sequence_number())
                return

            logger.info(action, logger.LogResult.success, "finished")
        except Exception as e:
            logger.error(action, logger.LogResult.fail, "error", str(e))
        finally:
            try:
                client_socket.close()
            except OSError:
                pass

    def _receive_init(self, client_socket):
        action = "handle-init"
        packet = receive_from(client_socket)
        if packet.type() != PacketType.INIT.value:
            raise ValueError(f"Expected INIT, got {packet.type()}")

        agency_id_str = packet.payload_to_string()
        try:
            agency_id = int(agency_id_str)
        except ValueError:
            send_ack(client_socket, packet.sequence_number(), b'ERROR')
            raise ValueError("Invalid agency ID")

        send_ack(client_socket, packet.sequence_number(), b'OK')
        logger.info(action, logger.LogResult.in_progress, "init-received", "agency_id", agency_id)
        return agency_id, packet.sequence_number() + 1

    def _receive_bets(self, client_socket, packet, seq_num):
        action = "receive-bets"
        try:
            bets_list = deserialize_batch(packet.payload())
            with self.lock:
                self.lottery.store_bets(bets_list)
        except Exception as e:
            logger.error(action, "Error", str(e))
            send_ack(client_socket, packet.sequence_number(), b'ERROR')
            return seq_num
        send_ack(client_socket, packet.sequence_number(), b'OK')
        logger.info(action, logger.LogResult.in_progress, "batch-stored", "count", len(bets_list), "seq", packet.sequence_number())
        return packet.sequence_number() + 1

    def _calculate_winners(self):
        action = "quorum-reached"
        with self.lock:
            all_bets = self.lottery.load_bets()
            self.winners = [b for b in all_bets if self.lottery.has_won(b)]
            logger.info(action, logger.LogResult.success,"winners", len(self.winners))
            

    def _send_winners(self, client_socket, seq_num, agency_id, winners):
        action = "send-winners"
        my_winners = [b for b in winners if b.agency_id == agency_id]
        logger.info(action, logger.LogResult.in_progress, "agency_id", agency_id, "count", len(my_winners))
        for bet in my_winners:
            send_response(client_socket, seq_num, bet)
            ack = receive_from(client_socket)
            if ack.type() != PacketType.ACK.value or ack.sequence_number() != seq_num:
                raise ValueError(f"ACK mismatch: expected {seq_num}")
            seq_num += 1
        return seq_num

    def run(self):
        action = "accept-connection"
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.server_host, self.server_port))
        self.server_socket.listen()
        self.server_socket.settimeout(1.0)  

        try:
            while not self.shutdown_event.is_set():
                try:
                    logger.info(action, logger.LogResult.in_progress)
                    client_socket, _ = self.server_socket.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break
                logger.info(action, logger.LogResult.success)

                t = threading.Thread(target=self._handle_client, args=(client_socket,))
                with self.active_clients_lock:
                    self.active_clients.append((client_socket, t))
                t.start()
        finally:
            try:
                self.server_socket.close()
            except OSError:
                pass

            with self.active_clients_lock:
                threads = [t for _, t in self.active_clients]
            for t in threads:
                t.join(timeout=2)
                if t.is_alive():
                    logger.warn("shutdown", "thread-still-alive")

            logger.info("server-shutdown", logger.LogResult.success)