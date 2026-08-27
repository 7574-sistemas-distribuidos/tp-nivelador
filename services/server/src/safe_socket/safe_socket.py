import socket


def recv_all(socket: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        chunk = socket.recv(size - len(chunks))
        chunks.extend(chunk)
    return bytes(chunks)


def send_all(socket: socket.socket, data: bytes) -> int:
    total_sent = 0
    while total_sent < len(data):
        total_sent += socket.send(data[total_sent:])
    return total_sent
