from dataclasses import dataclass

from lottery import Bet
from .message_header import MessageHeader, MessageType
from .parser import serialize_bet


@dataclass
class Message:
    header: MessageHeader
    payload: bytes = b""

    @staticmethod
    def ack() -> "Message":
        return Message(MessageHeader(MessageType.ACK, 0), b"")

    @staticmethod
    def winner(bet: Bet) -> "Message":
        payload = serialize_bet(bet)
        return Message(MessageHeader(MessageType.WINNER, len(payload)), payload)

    @staticmethod
    def finish() -> "Message":
        return Message(MessageHeader(MessageType.FINISH, 0), b"")
