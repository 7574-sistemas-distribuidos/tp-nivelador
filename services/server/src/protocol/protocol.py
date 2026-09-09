from enum import Enum
from .packet import Packet 
from lottery import Bet
from safe_socket import recv_all, send_all

INT32_BYTES = 4 
STRING_LEN_PREFIX_SIZE = 2 
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

def send_request(socket, seq_num, bet: Bet):
    packet = Packet(PacketType.REQUEST.value, seq_num, bet_to_bytes(bet))
    packet_bytes = packet.to_bytes()
    send_all(socket, packet_bytes)

def send_response(socket, seq_num, bet: Bet): 
    packet = Packet(PacketType.RESPONSE.value, seq_num, bet_to_bytes(bet))
    packet_bytes = packet.to_bytes()
    send_all(socket, packet_bytes)

def send_eof(socket, seq_num):
    packet = Packet(PacketType.EOF.value, seq_num, b'')
    packet_bytes = packet.to_bytes()
    send_all(socket, packet_bytes)

def send_ack(socket, seq_num, payload=b''):
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
 
def parse_bet_from_csv_line(line: str, agency_id: int):
    line = line.strip()
    if not line:
        raise ValueError("línea vacía")
    fields = line.split(',')
    if len(fields) != 5:
        raise ValueError(f"se esperaban 5 campos, se obtuvieron {len(fields)}")

    first_name = fields[0] 
    last_name = fields[1] 
    document = int(fields[2])
    birthdate = fields[3] 
    number = int(fields[4])
    return Bet(agency_id, first_name, last_name, document, birthdate, number)

def parse_csv_line_from_bet(bet: Bet): 
    return f"{bet.first_name},{bet.last_name},{bet.document},{bet.birthdate},{bet.number}"

def bet_to_bytes(bet: Bet):
    data = b''
    data += _string_to_bytes(str(bet.agency_id)) 
    data += _string_to_bytes(bet.first_name)
    data += _string_to_bytes(bet.last_name)
    data += bet.document.to_bytes(INT32_BYTES, byteorder='big')
    data += _string_to_bytes(bet.birthdate)
    data += bet.number.to_bytes(INT32_BYTES, byteorder='big')
    return data

def _string_to_bytes(s: str):
    b = s.encode('utf-8')
    return len(b).to_bytes(STRING_LEN_PREFIX_SIZE, byteorder='big') + b
 
def _bytes_to_string(data: bytes, cantBytes: int): 
    if len(data) < cantBytes:
        raise ValueError("prefijo de longitud incompleto")
    length = int.from_bytes(data[:cantBytes], byteorder='big')
    if len(data) < cantBytes + length:
        raise ValueError(f"string incompleto: esperado {length} bytes, disponibles {len(data)-cantBytes}")
    return data[cantBytes:cantBytes+length].decode('utf-8'), cantBytes + length

def bytes_to_bet(data: bytes) -> Bet: 
    idx = 0
    agency_str, step = _bytes_to_string(data[idx:], STRING_LEN_PREFIX_SIZE)
    idx += step
    first_name, step = _bytes_to_string(data[idx:], STRING_LEN_PREFIX_SIZE)
    idx += step
    last_name, step = _bytes_to_string(data[idx:], STRING_LEN_PREFIX_SIZE)
    idx += step
    document = int.from_bytes(data[idx:idx+INT32_BYTES], byteorder='big')
    idx += INT32_BYTES
    birthdate, step = _bytes_to_string(data[idx:], STRING_LEN_PREFIX_SIZE)
    idx += step
    number = int.from_bytes(data[idx:idx+INT32_BYTES], byteorder='big')
    agency_id = int(agency_str)
    return Bet(agency_id, first_name, last_name, document, birthdate, number)