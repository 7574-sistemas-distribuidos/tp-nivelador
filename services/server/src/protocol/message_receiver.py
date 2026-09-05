import socket
from safe_socket.safe_socket import recv_all
from enum import IntEnum
from protocol.bet import bet_from_bytes, bet_to_bytes
import logger


class MessageType(IntEnum):
    BET = 0
    ACK_BET = 1
    ALL_BETS_SENT = 2
    WINNERS = 3
    FINALIZE = 4



def read_bet_message(socket: socket.socket, lottery):
    bets = []
    payload_length = recv_all(socket, 4)
    if len(payload_length) < 4:
        raise Exception("Failed to read message length")
        
    message_length = int.from_bytes(payload_length, byteorder='big')
    payload = recv_all(socket, message_length)
    if len(payload) < message_length:
        raise Exception("Failed to read message payload")
    bets.append(bet_from_bytes(payload))
    lottery.store_bets(bets)
    return 1

def read_all_bets_sent_message(socket: socket.socket, lottery):
    logger.info("lottery", logger.LogResult.success, "all-bets-sent", "All bets have been sent")
    agency_id_bytes = recv_all(socket, 1)
    logger.info("lottery", logger.LogResult.success, "agency-id-bytes", agency_id_bytes)
    agency_id = int.from_bytes(agency_id_bytes, byteorder='big')
    logger.info("lottery", logger.LogResult.success, "agency-id", agency_id)
    winning_bets = []
    bets = lottery.load_bets()
    for bet in bets:
        if lottery.has_won(bet) and bet.agency_id == agency_id:
            winning_bets.append(bet_to_bytes(bet))
    logger.info("lottery", logger.LogResult.success, "winning-bets", winning_bets)
    for winning_bet in winning_bets:
        message = bytearray()
        message.append(MessageType.WINNERS)
        message.extend(winning_bet)
        socket.sendall(message)

    
    


def handle_message(socket: socket.socket, lottery):
    message_type_bytes = recv_all(socket, 1)
    message_type = MessageType(int.from_bytes(message_type_bytes))

    if message_type == MessageType.BET:
        return read_bet_message(socket, lottery)

    if message_type == MessageType.ALL_BETS_SENT:
        return read_all_bets_sent_message(socket,lottery)

    return None