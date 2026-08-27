import socket


def recv_all(socket: socket.socket, size):
    buffer = bytearray()
    while len(buffer) < size:
        chunk = socket.recv(size - len(buffer))
        buffer.extend(chunk)
    return bytes(buffer)


def send_all(socket: socket.socket, bytes):
    sent = 0
    while sent < len(bytes):
        sent += socket.send(memoryview(bytes)[sent:])
    return sent
