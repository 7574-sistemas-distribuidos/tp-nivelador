from protocol.bet import bet_from_bytes, bet_to_bytes, Bet


def unpack_bets(payload, bets_amount, agency_id) -> list[Bet]:
    bets = []
    offset = 0
    bets_unpacked = 0
    while bets_unpacked < bets_amount:
        bet_length = int.from_bytes(payload[offset:offset + 4],byteorder='big')
        offset += 4
        bet = bet_from_bytes(payload[offset: offset + bet_length], agency_id)
        offset += bet_length
        bets.append(bet)
        bets_unpacked +=1
    return bets
    