from services.server.src_frozen.lottery import Bet


def parse_bet(bytes: bytes) -> Bet:
    bet_line = str(payload)
    fields = bet_line.split(',')
    bet = Bet()
