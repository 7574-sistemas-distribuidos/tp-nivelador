"""
HEADER (3 bytes)
  tipo:          1 byte   (pocos valores)
  largo payload: 2 bytes

PAYLOAD BATCH (variable, tamaño = largo payload)
  agency:        1 byte   
  bets:          repetido, cada uno:
    largo nombre:  1 byte
    nombre:        N bytes   (UTF-8, variable)
    largo apellido:1 byte
    apellido:      M bytes   (UTF-8, variable)
    documento:     4 bytes
    cumpleaños:    4 bytes  (AAAAMMDD como un solo entero)
    number:        4 bytes

header type:
1 = BET       (cliente → servidor, una apuesta) 
4 = END       (cliente → servidor, servidor → cliente, "ya mandé todo")
2 = WINNER   (servidor → cliente, un winner)
3 = ACK   (cliente → servidor, servidor → cliente, confirmación de éxito, sin payload)
5 = BATCH  (cliente → servidor, una o más apuestas concatenadas)

"""
from dataclasses import dataclass

import safe_socket

BET = 1
WINNER = 2
ACK = 3
END = 4
BATCH = 5
_HEADER_SIZE = 3
_MAX_UINT16 = 0xFFFF  # límite de cualquier campo de 2 bytes del protocolo (largo de payload, contadores)
_MAX_PAYLOAD_SIZE = _MAX_UINT16
_MAX_FIELD_LENGTH = 0xFF


@dataclass
class BetMessage:
    nombre: str
    apellido: str
    documento: int
    cumpleanos: str
    number: int

    @staticmethod
    def decode(payload, pos: int = 0) -> tuple['BetMessage', int]:
        """"decodifica una apuesta a partir de pos, y devuelve la pos
        siguiente, para poder decodificar varias apuestas concatenadas 
        dentro de un mismo payload batch"""
        nombre, pos = _read_fixed_field(payload, pos)
        apellido, pos = _read_fixed_field(payload, pos)
        documento = int.from_bytes(payload[pos:pos+4], 'big')
        pos+=4
        cumpleanos = _decode_birthdate(payload[pos:pos+4])
        pos+=4
        number = int.from_bytes(payload[pos:pos+4], 'big')
        pos+=4
        return BetMessage(nombre, apellido, documento, cumpleanos, number), pos

@dataclass
class WinnerMessage:
    nombre: str
    apellido: str
    documento: int
    cumpleanos: str
    number: int

    def encode_payload(self) -> bytes:
        payload = (
            _encode_fixed_field(self.nombre) +
            _encode_fixed_field(self.apellido) +
            self.documento.to_bytes(4, 'big') +
            _encode_birthdate(self.cumpleanos) +
            self.number.to_bytes(4, 'big')
        )
        return payload


def read_message(sock) -> tuple[int, tuple[int, list[BetMessage]] | None]:
    """lee un mensje completo del socket, header + paylaod exacto, 
    y devuevle su tipo con los datos decodificados"""
    header = safe_socket.recv_all(sock, _HEADER_SIZE)
    tipo = int.from_bytes(header[0:1], 'big')
    largo_payload = int.from_bytes(header[1:3], 'big')
    payload = safe_socket.recv_all(sock, largo_payload)
    return tipo, decode_message(tipo, payload)

def read_expected(sock, expected_tipo) -> tuple[bool, tuple[int, list[BetMessage]] | None]:
    """espera leer un mensaje de un tipo puntual, salvo que llege END que 
    implica el fin de la comnicacion. 
    Devuelve (true, none) si fue END o (false, mensaje) si fue el tipo esperado 
    cualquier otro es un error"""
    tipo, data = read_message(sock)
    if tipo == END:
        return True, None
    if tipo != expected_tipo:
        raise ValueError(f"mensaje inesperado, se esperaba {expected_tipo} o END: tipo={tipo}")
    return False, data

def encode_end() -> bytes:
    return encode_message(END, b'')

def encode_ack() -> bytes:
    return encode_message(ACK, b'')

def encode_winner(winner: WinnerMessage) -> bytes:
    return encode_message(WINNER, winner.encode_payload())

def encode_message(tipo: int, payload: bytes) -> bytes:
    """arma el mensaje completo validando que el largo del payload
    no supere el maximo"""
    if len(payload) > _MAX_PAYLOAD_SIZE:
        raise ValueError(f"payload de {len(payload)} bytes excede el máximo de {_MAX_PAYLOAD_SIZE}")
    return tipo.to_bytes(1, 'big') + len(payload).to_bytes(2, 'big') + payload

def _encode_fixed_field(value: str) -> bytes:
    """"codifica un campo de largo variable con 1 byte de largo + el contenido"""
    value_bytes = value.encode('utf-8')
    if len(value_bytes) > _MAX_FIELD_LENGTH:
        raise ValueError(f"campo de {len(value_bytes)} bytes excede el máximo de {_MAX_FIELD_LENGTH}")
    return len(value_bytes).to_bytes(1, 'big') + value_bytes

def _encode_birthdate(cumpleanos) -> bytes:
    " de AAAA-MM-DD a AAAAMMDD bytes"
    cumpleanos_int = int(cumpleanos.replace("-", ""))
    return cumpleanos_int.to_bytes(4, 'big')

def decode_batch(payload) -> tuple[int, list[BetMessage]]:
    """decodifica el payload de un mensaje BATCH: el agency id, seguido
    de todoas las BETs concatenadas"""
    agency = int.from_bytes(payload[0:1], 'big')
    pos = 1 
    bets = []
    while pos < len(payload):
        bet, pos = BetMessage.decode(payload, pos)
        bets.append(bet)
    return agency, bets

def _decode_birthdate(birthday_bytes) -> str:
    "de AAAAMMDD a AAAA-MM-DD"
    birthday = int.from_bytes(birthday_bytes, 'big')
    birthday_str = str(birthday)
    if len(birthday_str) != 8:
        raise ValueError(f"fecha de nacimiento inválida: se esperaban 8 dígitos (AAAAMMDD), se recibió {birthday_str!r}")
    year = birthday_str[:4]
    month = birthday_str[4:6]
    day = birthday_str[6:8]
    return f"{year}-{month}-{day}"

def decode_message(tipo, payload) -> tuple[int, list[BetMessage]] | None:
    if tipo == BATCH:
        return decode_batch(payload)
    elif tipo == ACK:
        return None
    elif tipo == END:
        return None
    else:
        raise ValueError(f"Tipo de mensaje desconocido: {tipo}")

def _read_fixed_field(payload: bytes, pos: int) -> tuple[str, int]:
    """lee el byte de largo y despues esa cantidad de bytes de contenido"""
    length = payload[pos]
    pos+=1
    value_bytes = payload[pos:pos+length]
    pos+=length
    return value_bytes.decode('utf-8'), pos


