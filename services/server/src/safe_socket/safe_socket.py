import socket


def recv_all(socket: socket.socket, size):
    data = b""

    while len(data) < size:
        chunk = socket.recv(size - len(data))

        if not chunk:
            return b""

        data += chunk

    return data


def send_all(socket: socket.socket, bytes):
    sent = 0

    while sent < len(bytes):
        sent += socket.send(bytes[sent:])
