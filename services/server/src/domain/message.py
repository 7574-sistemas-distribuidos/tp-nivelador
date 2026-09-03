from dataclasses import dataclass


@dataclass
class Message:
    type: MessageType
    payload: bytes = b""
