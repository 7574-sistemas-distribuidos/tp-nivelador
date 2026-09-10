from lottery import Bet
STRING_LEN_PREFIX_SIZE = 2 
INT32_BYTES = 4

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