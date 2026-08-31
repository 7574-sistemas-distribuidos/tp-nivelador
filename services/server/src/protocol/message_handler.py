import socket
from safe_socket.safe_socket import recv_all, send_all


def read_message(socket: socket.socket):
    payload_length = recv_all(socket, 4)
    if payload_length == b'':
        return None
    if len(payload_length) < 4:
        raise Exception("Failed to read message length")
    
    message_length = int.from_bytes(payload_length, byteorder='big')
    payload = recv_all(socket, message_length)
    if len(payload) < message_length:
        raise Exception("Failed to read message payload")
    

    return payload