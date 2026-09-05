from lottery.bet import Bet
import logger


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


def bet_to_bytes(bet: Bet) -> bytes:
    logger.info("lottery", logger.LogResult.success, "bet-to-bytes", bet.__dict__)
    first_name_bytes = bet.first_name.encode('utf-8')
    last_name_bytes = bet.last_name.encode('utf-8')

    data = bytearray()
    data.append(len(first_name_bytes))
    logger.info("lottery", logger.LogResult.success, "first-name-bytes", first_name_bytes)
    data.extend(first_name_bytes)
    logger.info("lottery", logger.LogResult.success, "last-name-bytes", last_name_bytes)
    data.append(len(last_name_bytes))
    logger.info("lottery", logger.LogResult.success, "last-name-bytes", last_name_bytes)
    data.extend(last_name_bytes)
    logger.info("lottery", logger.LogResult.success, "document-bytes", bet.document.to_bytes(4, byteorder='big'))
    data.extend(bet.document.to_bytes(4, byteorder='big'))

    final_data = bytearray()
    total_length = len(data)
    final_data.extend(total_length.to_bytes(4, byteorder='big'))
    final_data.extend(data)
    logger.info("lottery", logger.LogResult.success, "bet-to-bytes-final", final_data)
    return bytes(final_data)    
