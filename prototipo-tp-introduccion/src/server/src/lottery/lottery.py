import csv
from collections.abc import Iterator
from .bet import Bet

_LOTTERY_WINNER_NUMBER = 7574


class Lottery:
    def __init__(self, storage_path) -> None:
        self.storage_path = storage_path

    def has_won(self, bet: Bet) -> bool:
        return bet.number == _LOTTERY_WINNER_NUMBER

    def store_bets(self, bets: list[Bet]) -> None:
        with open(self.storage_path, "a+") as file:
            writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
            for bet in bets:
                writer.writerow(
                    [
                        bet.agency_id,
                        bet.first_name,
                        bet.last_name,
                        bet.document,
                        bet.birthdate,
                        bet.number,
                    ]
                )

    def load_bets(self) -> Iterator[Bet]:
        with open(self.storage_path, "r") as file:
            reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
            for row in reader:
                [agency_id, first_name, last_name, document, birthdate, number] = row
                yield Bet(
                    int(agency_id),
                    first_name,
                    last_name,
                    document,
                    birthdate,
                    int(number),
                )
