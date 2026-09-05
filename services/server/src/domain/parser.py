from lottery import Bet

_BET_FIELDS_AMOUNT = 6
_ENCODING = "utf-8"


# 1,Santiago Lionel,Lorca,30904465,1999-03-17,7574
def parse_bet(payload: bytes) -> Bet:
    fields = payload.decode(_ENCODING).strip().split(",")
    if len(fields) != _BET_FIELDS_AMOUNT:
        raise ValueError(
            f"invalid bet payload: expected {_BET_FIELDS_AMOUNT} fields, got {len(fields)}"
        )

    agency_id, first_name, last_name, document, birthdate, number = fields
    return Bet(
        int(agency_id),
        first_name,
        last_name,
        int(document),
        birthdate,
        int(number),
    )


def parse_agency_id(payload: bytes) -> int:
    return int(payload.decode(_ENCODING).strip())


# Santiago Lionel,Lorca,30904465,1999-03-17,7574
def serialize_bet(bet: Bet) -> bytes:
    fields = [
        bet.first_name,
        bet.last_name,
        str(bet.document),
        bet.birthdate,
        str(bet.number),
    ]
    return ",".join(fields).encode(_ENCODING)
