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

    def _handle_client(self, client_socket):
        action = "handle-client"
        seq_num = INIT_SEQ_NUM
        try:
            logger.info(action, logger.LogResult.in_progress)

            agency_id, seq_num = self._receive_init(client_socket)
            logger.info(action, logger.LogResult.in_progress, "agency_id", agency_id)
            while True:
                packet = receive_from(client_socket)
                if packet.type() == PacketType.REQUEST.value:
                    seq_num = self._receive_bets(client_socket, packet, seq_num)
                elif packet.type() == PacketType.EOF.value:
                    send_ack(client_socket, packet.sequence_number(), b'OK')
                    logger.info(action, logger.LogResult.in_progress, "eof-received")
                    seq_num = packet.sequence_number() + 1
                    break

            self.barrier.wait()

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
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.server_host, self.server_port))
            server_socket.listen()
            while True:
                try:
                    logger.info(action, logger.LogResult.in_progress)
                    client_socket, _ = server_socket.accept()
                except Exception as e:
                    logger.error(action, logger.LogResult.fail)
                    continue  # raise e
                logger.info(action, logger.LogResult.success)
                threading.Thread(target=self._handle_client, args=(client_socket,)).start()
