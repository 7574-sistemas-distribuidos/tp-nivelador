import socket
import logger 
import lottery
from protocol import PacketType, receive_from, send_response


LENGTH_MESSAGE_SIZE = 4
STORAGE_FILE = "bets"
FILE_EXTENSION = ".csv"

class Server:
    def __init__(self, server_host: str, server_port: int) -> None:
        self.server_host = server_host
        self.server_port = server_port

    def _handle_client(self, client_socket):
        action = "handle-client"
        storage_path = STORAGE_FILE+FILE_EXTENSION
        with open(storage_path, 'w') as f:
            pass
        bets = lottery.Lottery(storage_path)
        message_amount = 0
        agency_id = None
        try:
            logger.info(action, logger.LogResult.in_progress)
            while True:
                packet = receive_from(client_socket)
                logger.info("debug-packet", "type", packet.type(), "size", packet.payload_size())
                if packet.type() == PacketType.INIT.value:
                    agency_id = int(packet.payload_to_string())
                elif packet.type() == PacketType.REQUEST.value:
                    data = packet.payload_to_string().split(',')
                    if len(data) != 5:
                        # poner logger error
                        continue
                    first_name = data[0]
                    last_name = data[1]
                    document = int(data[2])
                    birthdate = data[3]
                    number = int(data[4])
                    bet = lottery.Bet(agency_id, first_name, last_name, document, birthdate, number)
                    bets.store_bets([bet])
                    message_amount += 1
                    logger.info(action, logger.LogResult.in_progress, "bets-stored", message_amount)
                elif packet.type() == PacketType.EOF.value:
                    # recibo el fin de las apuestas
                    # calculo el ganador
                    all_bets = list(bets.load_bets())
                    winners = [bet for bet in all_bets if bets.has_won(bet)]
                    # serializar a csv los winners
                    winners_str = ''
                    for w in winners:
                        winners_str += f"{w.first_name},{w.last_name},{w.document},{w.birthdate},{w.number}\n"
                    send_response(client_socket, winners_str.encode('utf-8'))
                    logger.info(action, logger.LogResult.success, "winners-sent", len(winners))
                    break
                else:
                    # poner logger error
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
