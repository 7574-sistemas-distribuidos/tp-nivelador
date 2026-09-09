import socket
import logger 
import lottery
from protocol import (PacketType, receive_from, send_response, send_ack,
                      send_eof, send_init, send_request,
                      bytes_to_bet, parse_csv_line_from_bet)

LENGTH_MESSAGE_SIZE = 4
BETS_FILE = "bets.csv"
INIT_SEQ_NUM = 0

class Server:
    def __init__(self, server_host: str, server_port: int) -> None:
        self.server_host = server_host
        self.server_port = server_port

    def _handle_client(self, client_socket):
        action = "handle-client"
        open(BETS_FILE, 'w').close()   #limpiamos el archivo al iniciar una conexion
        bets = lottery.Lottery(BETS_FILE)
        seq_num = INIT_SEQ_NUM
        try:
            logger.info(action, logger.LogResult.in_progress)

            agency_id, seq_num = self._receive_init(client_socket)
            logger.info(action, logger.LogResult.in_progress, "agency_id", agency_id)
            while True:
                packet = receive_from(client_socket)
                if packet.type() == PacketType.REQUEST.value:
                    seq_num, bets = self._receive_bets(client_socket, packet, bets, seq_num)
                elif packet.type() == PacketType.EOF.value:
                    send_ack(client_socket, packet.sequence_number(), b'OK')
                    logger.info(action, logger.LogResult.in_progress, "eof-received")
                    seq_num = packet.sequence_number() + 1
                    break
                else:
                    logger.error("unknown-packet-type", packet.type())
                    send_ack(client_socket, packet.sequence_number(), b'UNKNOWN')
                    return

            seq_num = self._send_winners(client_socket, seq_num, bets)

            send_eof(client_socket, seq_num)
            ack = receive_from(client_socket)
            if ack.type() != PacketType.ACK.value or ack.sequence_number() != seq_num:
                logger.error("final-ack-mismatch", "expected", seq_num, "received", ack.sequence_number())
                return

            logger.info(action, logger.LogResult.success, "finished")

        except Exception as e:
            logger.error(action, logger.LogResult.fail, "error", str(e))
            raise

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

    def _receive_bets(self, client_socket, packet, bets, seq_num):
        action = "receive-bets"
        try:
            bet = bytes_to_bet(packet.payload())
        except Exception as e:
            logger.error("parse-error", str(e))
            send_ack(client_socket, packet.sequence_number(), b'ERROR')
            raise

        bets.store_bets([bet])
        send_ack(client_socket, packet.sequence_number(), b'OK')
        logger.info(action, logger.LogResult.in_progress, "bet-stored", "seq", packet.sequence_number())
        seq_num = packet.sequence_number() + 1
        return seq_num, bets

    def _send_winners(self, client_socket, seq_num, bets):
        action = "send-winners"
        all_bets = bets.load_bets()
        winners = [bet for bet in all_bets if bets.has_won(bet)]
        logger.info(action, logger.LogResult.in_progress, "winners", len(winners))

        for bet in winners:
            send_response(client_socket, seq_num, bet)
            ack = receive_from(client_socket)
            if ack.type() != PacketType.ACK.value or ack.sequence_number() != seq_num:
                raise ValueError(f"ACK mismatch: expected {seq_num}, got {ack.sequence_number()}")
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

                self._handle_client(client_socket)
