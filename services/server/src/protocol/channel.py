import safe_socket

from protocol.errors import ProtocolError
from protocol.messages.deserialization.incoming import (
    FinalizeBetsSendingMessage,
)
from protocol.messages.deserialization.incoming import FilledBetsMessage, StartBetsSendingMessage

_TYPE_BYTES = 1
_LENGTH_BYTES = 2

_MESSAGE_BY_TYPE = {
    b"\x01": StartBetsSendingMessage,
    b"\x02": FilledBetsMessage,
    b"\x03": FinalizeBetsSendingMessage,
}


class MessageChannel:
    def __init__(self, client_socket):
        self._socket = client_socket

    def receive(self):
        message_type = safe_socket.recv_all(self._socket, _TYPE_BYTES)
        length = int.from_bytes(
            safe_socket.recv_all(self._socket, _LENGTH_BYTES), byteorder="big"
        )
        payload = safe_socket.recv_all(self._socket, length) if length else b""

        message_class = _MESSAGE_BY_TYPE.get(message_type)
        if message_class is None:
            raise ProtocolError(f"unknown message type 0x{message_type.hex()}")
        return message_class.from_bytes(payload)

    def send(self, message):
        payload = message.payload()
        length = len(payload).to_bytes(_LENGTH_BYTES, byteorder="big")
        total_frame_bytes = message.type() + length + payload
        safe_socket.send_all(self._socket, total_frame_bytes)
