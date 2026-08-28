import socket
import logger


def recv_all(socket: socket.socket, size):
    chunks = []
    bytes_received = 0

    while bytes_received < size:
        chunk = socket.recv(size - bytes_received)
        if not chunk:
            logger.info("saliendo de recv-all por EOF",logger.LogResult.success, ", bytes_received", bytes_received)
            break

        chunks.append(chunk)
        bytes_received += len(chunk)
        logger.info("recv-all", logger.LogResult.in_progress, "bytes-received", chunk)
        
    return b''.join(chunks)[:bytes_received]



def send_all(socket: socket.socket, bytes):
    bytes_to_send = len(bytes)
    bytes_sent = 0
    while bytes_sent < bytes_to_send:
        n = socket.send(bytes[bytes_sent:])
        if n == -1:
            raise Exception("Socket error during write operation")
        if n == 0:
            break
        bytes_sent += n
        logger.info("send-all", logger.LogResult.in_progress, "bytes-sent", bytes_sent)
    return bytes_sent
