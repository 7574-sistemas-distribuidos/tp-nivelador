import socket


def recv_all(socket: socket.socket, size):
    total = 0 
    buff = bytearray(size)
    while total < size:
        try:
            n = socket.recv(size - total)
        except socket.error:
            raise RuntimeError("Socket connection closed")

        buff[total:total+len(n)] = n

        if len(n) == 0:
            raise RuntimeError("Socket connection closed")

        total += len(n)
    return buff


def send_all(socket: socket.socket, bytes):
    total = 0 
    while total < len(bytes):
        try:
            n = socket.send(bytes[total:])
        except socket.error:
            raise RuntimeError("Socket connection closed")

        total += n
    return total
