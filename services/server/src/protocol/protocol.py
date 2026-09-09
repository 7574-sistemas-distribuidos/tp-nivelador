from enum import Enum
from .packet import Packet 
from safe_socket import recv_all, send_all

class PacketType(Enum):
    REQUEST = 0
    RESPONSE = 1
    EOF = 2
    INIT = 3
    ACK = 4


def send_init(socket, seq_num, payload):
    packet = Packet(PacketType.INIT.value, seq_num, payload)
    packet_bytes = packet.to_bytes()
    send_all(socket, packet_bytes)

def send_request(socket, seq_num, payload):
    packet = Packet(PacketType.REQUEST.value, seq_num, payload)
    packet_bytes = packet.to_bytes()
    send_all(socket, packet_bytes)

def send_response(socket, seq_num, payload):
    packet = Packet(PacketType.RESPONSE.value, seq_num, payload)
    packet_bytes = packet.to_bytes()
    send_all(socket, packet_bytes)

def send_eof(socket, seq_num):
    packet = Packet(PacketType.EOF.value, seq_num, b'')
    packet_bytes = packet.to_bytes()
    send_all(socket, packet_bytes)

def send_ack(socket, seq_num, payload):
    packet = Packet(PacketType.ACK.value, seq_num, payload)
    packet_bytes = packet.to_bytes()
    send_all(socket, packet_bytes)

def receive_from(sock):
    header = recv_all(sock, Packet.HEADER_SIZE)
    if not header:
        raise RuntimeError("Socket connection error")
    packet_type = int.from_bytes(header[:1], 'big')
    seq_number = int.from_bytes(header[1:5], 'big')
    payload_size = int.from_bytes(header[5:], 'big')
    payload = recv_all(sock, payload_size)
    return Packet(packet_type, seq_number, payload) 
 