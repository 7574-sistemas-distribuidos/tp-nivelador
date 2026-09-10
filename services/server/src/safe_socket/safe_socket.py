import socket


def recv_all(sock: socket.socket, size):
    total = 0 
    buff = bytearray(size)
    while total < size:
        try:
            n = sock.recv(size - total)
        except socket.error:
            raise RuntimeError("Socket connection closed")

        buff[total:total+len(n)] = n

        if len(n) == 0:
            raise RuntimeError("Socket connection closed")

        total += len(n)
    return buff


def send_all(sock: socket.socket, bytes):
    total = 0 
    while total < len(bytes):
        try:
            n = sock.send(bytes[total:])
        except socket.error:
            raise RuntimeError("Socket connection closed")

        total += n
    return total
