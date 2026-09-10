import struct
import socket
from safe_socket import send_all, recv_all

MSG_BET = 1
MSG_ACK = 2
MSG_END_BETS = 3
MSG_WINNERS = 4

# Header: 1 byte msg_type (uint8) + 4 bytes length (uint32 big-endian) = 5 bytes
_HEADER_FORMAT = "!BI"
_HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)


def send_msg(sock: socket.socket, msg_type: int, payload: bytes = b"") -> None:
    """Empaqueta la cabecera y envía el mensaje completo por el socket."""
    header = struct.pack(_HEADER_FORMAT, msg_type, len(payload))
    send_all(sock, header + payload)


def recv_msg(sock: socket.socket) -> tuple[int, bytes] | tuple[None, None]:
    """Recibe un mensaje con cabecera de tipo y longitud fija.

    Retorna (msg_type, payload). Si la conexión se cerró limpiamente al inicio,
    retorna (None, None).
    """
    header_bytes = recv_all(sock, _HEADER_SIZE)
    if not header_bytes:
        return None, None
    msg_type, length = struct.unpack(_HEADER_FORMAT, header_bytes)
    payload = recv_all(sock, length) if length > 0 else b""
    return msg_type, payload
