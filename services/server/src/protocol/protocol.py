import socket
from typing import Tuple

import safe_socket
from domain.message import Message
from domain.message_header import HEADER_SIZE, MessageHeader


def send_message(connection: socket.socket, message: Message) -> None:
    safe_socket.send_all(connection, message.header.serialize())

    if message.header.payload_len > 0:
        safe_socket.send_all(connection, message.payload)


def receive_message(connection: socket.socket) -> Tuple[MessageHeader, bytes]:
    header_bytes = safe_socket.recv_all(connection, HEADER_SIZE)
    header = MessageHeader.deserialize(header_bytes)
    payload = safe_socket.recv_all(connection, header.payload_len)

    return header, payload


