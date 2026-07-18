import socket

#TODO: Complete with a short-read/short-write tolerant implementation

def recv_all(socket: socket.socket, size):
    return socket.recv(size)


def send_all(socket: socket.socket, bytes):
    return socket.send(bytes)
