from lottery.bet import Bet



def bet_from_bytes(data: bytes) -> Bet:
    offset = 0
    agency_id = data[offset]
    offset += 1
    first_name_length = data[offset]
    offset += 1
    first_name = data[offset:offset + first_name_length].decode('utf-8')
    offset += first_name_length
    last_name_length = data[offset]
    offset += 1
    last_name = data[offset:offset + last_name_length].decode('utf-8')
    offset += last_name_length
    document= int.from_bytes(data[offset:offset + 4], byteorder='big')
    offset += 4
    birthdat_length = data[offset]
    offset += 1
    birthdate = data[offset:offset + birthdat_length].decode('utf-8')
    offset += birthdat_length
    number = int.from_bytes(data[offset:offset + 2], byteorder='big')
    return Bet(
        agency_id=agency_id,
        first_name=first_name,
        last_name=last_name,
        document=document,
        birthdate=birthdate,
        number=number
    )    
