from dataclasses import dataclass

from .message_header import MessageHeader, MessageType


@dataclass
class Message:
    header: MessageHeader
    payload: bytes = b""

    @staticmethod
    def ack() -> "Message":
        return Message(MessageHeader(MessageType.ACK, 0), b"")
