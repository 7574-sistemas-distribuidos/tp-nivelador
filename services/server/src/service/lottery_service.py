import os
from collections.abc import Iterator

from lottery import Bet, Lottery

BETS_FILE_NAME = "bets.csv"


class LotteryService:
    def __init__(self, storage_dir: str) -> None:
        self._lottery = Lottery(os.path.join(storage_dir, BETS_FILE_NAME))

    def register_bets(self, bets: list[Bet]) -> None:
        self._lottery.store_bets(bets)

    def winners_for(self, agency_id: int) -> Iterator[Bet]:
        for bet in self._lottery.load_bets():
            if self._lottery.has_won(bet) and bet.agency_id == agency_id:
                yield bet
