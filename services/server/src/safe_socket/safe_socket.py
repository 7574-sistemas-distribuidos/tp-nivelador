import socket


def recv_all(sock: socket_module.socket, size: int) -> bytes:
    buffer = bytearray()
    while len(buffer) < size:
        chunk = sock.recv(size - len(buffer))
        if not chunk:
            raise ConnectionError("socket connection broken while receiving")
        buffer.extend(chunk)
    return bytes(buffer)


def send_all(sock: socket_module.socket, data: bytes) -> None:
    sent = 0
    while sent < len(data):
        n = sock.send(memoryview(data)[sent:])
        if n == 0:
            raise ConnectionError("socket connection broken while sending")
        sent += n
