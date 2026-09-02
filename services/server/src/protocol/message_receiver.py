import socket
from safe_socket.safe_socket import recv_all
from enum import IntEnum
from protocol.bet import bet_from_bytes
import logger


class MessageType(IntEnum):
    BET = 0
    ACK_BET = 1
    ALL_BETS_SENT = 2



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

def read_all_bets_sent_message(lottery):
    winning_bets = []
    bets = lottery.load_bets()
    for bet in bets:
        if lottery.has_won(bet):
            winning_bets.append(bet)
    logger.info("lottery", logger.LogResult.success, "winning-bets", [bet.__dict__ for bet in winning_bets])
    return winning_bets


def handle_message(socket: socket.socket, lottery):
    message_type_bytes = recv_all(socket, 1)
    message_type = MessageType(int.from_bytes(message_type_bytes))

    if message_type == MessageType.BET:
        return read_bet_message(socket, lottery)

    if message_type == MessageType.ALL_BETS_SENT:
        return read_all_bets_sent_message(lottery)

    return None