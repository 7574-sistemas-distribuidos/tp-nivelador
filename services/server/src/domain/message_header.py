import struct
from enum import IntEnum
from typing import Tuple

import safe_socket


class MessageType(IntEnum):
    REGISTER_AGENCY = 1
    ACK = 2
    BET = 3
    AWAITING_WINNERS = 4
    WINNER = 5


MESSAGE_TYPE_SIZE = 1
PAYLOAD_LEN_SIZE = 4
HEADER_SIZE = MESSAGE_TYPE_SIZE + PAYLOAD_LEN_SIZE

_HEADER_STRUCT_FORMAT = ">BI"  # big-endian: u8 (type) + u32 (payload_len)


class Header:
    def __init__(self, msg_type: MessageType, payload_len: int) -> None:
        self.type = msg_type
        self.payload_len = payload_len

    def serialize(self) -> bytes:
        return struct.pack(_HEADER_STRUCT_FORMAT, self.type, self.payload_len)

    @staticmethod
    def deserialize(buf: bytes) -> "Header":
        if len(buf) != HEADER_SIZE:
            raise ValueError(
                f"invalid header size: expected {HEADER_SIZE} bytes, got {len(buf)}"
            )
        msg_type_value, payload_len = struct.unpack(_HEADER_STRUCT_FORMAT, buf)
        return Header(MessageType(msg_type_value), payload_len)

