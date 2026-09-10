from lottery.bet import Bet


def bet_from_bytes(data: bytes,agency_id) -> Bet:
    offset = 0
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
    number = int.from_bytes(data[offset:offset + 4], byteorder='big')

    return Bet(
        agency_id=agency_id,
        first_name=first_name,
        last_name=last_name,
        document=document,
        birthdate=birthdate,
        number=number
    )


def bet_to_bytes(bet: Bet) -> bytes:
    first_name_bytes = bet.first_name.encode('utf-8')
    last_name_bytes = bet.last_name.encode('utf-8')
    birthdate_bytes = str(bet.birthdate).encode('utf-8')

    data = bytearray()
    
    data.append(len(first_name_bytes))
    data.extend(first_name_bytes)

    
    data.append(len(last_name_bytes))
    data.extend(last_name_bytes)
    
    data.extend(int(bet.document).to_bytes(4, byteorder='big'))
    
    data.append(len(birthdate_bytes))
    data.extend(birthdate_bytes)
    
    data.extend(int(bet.number).to_bytes(4, byteorder='big'))

    final_data = bytearray()
    total_length = len(data)
    final_data.extend(total_length.to_bytes(4, byteorder='big'))
    final_data.extend(data)
    

    return bytes(final_data)  
