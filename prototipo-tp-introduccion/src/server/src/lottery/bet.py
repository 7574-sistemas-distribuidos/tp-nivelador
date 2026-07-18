from dataclasses import dataclass


@dataclass
class Bet:
    agency_id: int
    first_name: str
    last_name: str
    document: int
    birthdate: str
    number: int
