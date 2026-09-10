import socket

# Short-read/short-write tolerant implementation


def recv_all(socket: socket.socket, size):
    if size <= 0:
        return b''
    total_bytes_received = 0
    buffer = b''
    while total_bytes_received < size:
        received = socket.recv(size - total_bytes_received)
        if not received:
            raise RuntimeError("Socket connection error")
        buffer += received
        total_bytes_received += len(received)
    return buffer


def send_all(socket: socket.socket, bytes):
    total_bytes_sent = 0
    while total_bytes_sent < len(bytes):
        sent = socket.send(bytes[total_bytes_sent:])
        total_bytes_sent += sent
    return total_bytes_sent