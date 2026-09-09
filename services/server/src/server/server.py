import socket
import logger 
import lottery
from protocol import PacketType, receive_from, send_response, send_ack


LENGTH_MESSAGE_SIZE = 4
BETS_FILE = "bets.csv"

class Server:
    def __init__(self, server_host: str, server_port: int) -> None:
        self.server_host = server_host
        self.server_port = server_port

    def _handle_client(self, client_socket):
        action = "handle-client"
        open(BETS_FILE, 'w').close()   #limpiamos el archivo al iniciar una conexion
        bets = lottery.Lottery(BETS_FILE)
        agency_id = None
        last_valid_seq_num = -1
        try:
            logger.info(action, logger.LogResult.in_progress)
            while True:
                packet = receive_from(client_socket)
                logger.info("debug-packet", "type", packet.type(), "size", packet.payload_size())
                if packet.type() == PacketType.INIT.value:
                    agency_id = int(packet.payload_to_string())
                    send_ack(client_socket, packet.sequence_number(), packet.payload())
                    logger.info(action, logger.LogResult.in_progress, "init-received", "agendy-id: ", agency_id)
                elif packet.type() == PacketType.REQUEST.value:
                    data = packet.payload_to_string().split(',')
                    if len(data) != 5:
                        logger.error("invalid bet line: ", packet.payload_to_string())
                        send_ack(client_socket, last_valid_seq_num, b'ERROR')
                        continue
                    first_name, last_name, document, birthdate, number = data[0], data[1], int(data[2]), data[3], int(data[4])

                    bet = lottery.Bet(agency_id, first_name, last_name, document, birthdate, number)
                    bets.store_bets([bet])
                    logger.info(action, logger.LogResult.in_progress, "sequence number received: ", last_valid_seq_num)
                    send_ack(client_socket, packet.sequence_number(), packet.payload())
                elif packet.type() == PacketType.EOF.value:
                    send_ack(client_socket, packet.sequence_number(), packet.payload())
                    all_bets = list(bets.load_bets())
                    winners = [bet for bet in all_bets if bets.has_won(bet)]
                    winners_str = ''
                    for w in winners:
                        winners_str += f"{w.first_name},{w.last_name},{w.document},{w.birthdate},{w.number}\n"
                    send_response(client_socket, 0, winners_str.encode('utf-8'))
                    logger.info(action, logger.LogResult.success, "winners-sent", len(winners))
                    break
                else:
                    logger.error("unknown packet type: ", packet.type())
                    send_ack(client_socket, packet.sequence_number(), b'UNKNOWN')
                    break
        except Exception as e:
            logger.error(action, logger.LogResult.fail, "error", str(e))
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
                    continue  # raise e
                logger.info(action, logger.LogResult.success)

                self._handle_client(client_socket)
