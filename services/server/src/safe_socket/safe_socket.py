import socket

def recv_all(socket: socket.socket, size):
    chunks = []
    bytes_received = 0

    while bytes_received < size:
        chunk = socket.recv(size - bytes_received)
        if not chunk:
            break

        chunks.append(chunk)
        bytes_received += len(chunk)
    return b''.join(chunks)[:bytes_received]



def send_all(socket: socket.socket, bytes):
    bytes_to_send = len(bytes)
    bytes_sent = 0
    while bytes_sent < bytes_to_send:
        n = socket.send(bytes[bytes_sent:])
        if n == -1:
            raise Exception("Socket error during write operation")
        bytes_sent += n
    return bytes_sent
