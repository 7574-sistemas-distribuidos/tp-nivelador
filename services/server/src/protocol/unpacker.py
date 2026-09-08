from protocol.bet import bet_from_bytes, bet_to_bytes, Bet
import logger


def unpack_bets(payload, bets_amount, agency_id) -> list[Bet]:
    bets = []
    offset = 0
    bets_unpacked = 0
    while bets_unpacked < bets_amount:
        logger.info("unpack_bets", logger.LogResult.in_progress, "bets-unpacking", f"Unpacking bet {bets_unpacked + 1} of {bets_amount} for agency {agency_id}")
        bet_length = int.from_bytes(payload[offset:offset + 4],byteorder='big')
        offset += 4
        bet = bet_from_bytes(payload[offset: offset + bet_length], agency_id)
        offset += bet_length
        bets.append(bet)
        bets_unpacked +=1
    logger.info("unpack_bets", logger.LogResult.success, "bets-unpacked", f"Unpacked {len(bets)} bets for agency {agency_id}")
    return bets
    