from .bet_handler import bet_to_bytes, bytes_to_bet

BATCH_PREFIX_BYTES = 2

def serialize_batch(bets: list): 
    batch = b''
    len_bets_bytes= len(bets)
    batch += len_bets_bytes.to_bytes(BATCH_PREFIX_BYTES, 'big')
    for b in bets:
        bet_bytes = bet_to_bytes(b)
        batch += len(bet_bytes).to_bytes(BATCH_PREFIX_BYTES, 'big')
        batch += bet_bytes

    return batch

def deserialize_batch(data: bytes) -> list:
    if len(data) < BATCH_PREFIX_BYTES:
        raise ValueError("not enough data")

    idx = 0 
    total_bets = int.from_bytes(data[idx:idx+BATCH_PREFIX_BYTES], 'big')
    idx += BATCH_PREFIX_BYTES

    bets = []
    for i in range(total_bets): 
        if idx + BATCH_PREFIX_BYTES > len(data):
            raise ValueError("not enough data")
        bet_length = int.from_bytes(data[idx:idx+BATCH_PREFIX_BYTES], 'big')
        idx += BATCH_PREFIX_BYTES

        if idx + bet_length > len(data):
            raise ValueError("not enough data")
        bet_bytes = data[idx:idx+bet_length]
        idx += bet_length
 
        bets.append(bytes_to_bet(bet_bytes))
 
    return bets