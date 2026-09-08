
from lottery.bet import Bet
from protocol.message_type import MessageType
from protocol.bet import bet_to_bytes

def generate_winning_bets_packet(winning_bets: list[Bet]) -> bytearray:
    packet = bytearray()
    packet.append(MessageType.WINNERS)
    winners = bytearray()
    for winning_bet in winning_bets:
        winners.extend(bet_to_bytes(winning_bet))
    payload_length = len(winners) + 4
    packet.extend(payload_length.to_bytes(4, byteorder='big'))
    winning_bets_amount = len(winning_bets)
    packet.extend(winning_bets_amount.to_bytes(4, byteorder='big'))
    packet.extend(winners)
    return packet