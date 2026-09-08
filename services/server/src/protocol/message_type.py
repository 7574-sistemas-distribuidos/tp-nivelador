from enum import IntEnum


class MessageType(IntEnum):
    BET = 0
    ACK_BET = 1
    ALL_BETS_SENT = 2
    WINNERS = 3
    FINALIZE = 4
