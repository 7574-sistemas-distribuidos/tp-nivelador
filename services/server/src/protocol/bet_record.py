from lottery.bet import Bet


class BetRecord:
    _DOCUMENT_BYTES = 4
    _NUMBER_BYTES = 2
    _BIRTHDATE_BYTES = 10
    _NAME_LENGTH_BYTES = 1

    def __init__(self, document, number, birthdate, first_name, last_name):
        birthdate_in_bytes = birthdate.encode("utf-8")
        if len(birthdate_in_bytes) != self._BIRTHDATE_BYTES:
            raise ValueError(
                f"birthdate must be exactly {self._BIRTHDATE_BYTES} bytes, "
                f"got {len(birthdate_in_bytes)}: {birthdate!r}"
            )
        self._document = document
        self._number = number
        self._birthdate = birthdate
        self._first_name = first_name
        self._last_name = last_name

    @classmethod
    def from_bet(cls, bet: Bet):
        return cls(
            document=bet.document,
            number=bet.number,
            birthdate=bet.birthdate,
            first_name=bet.first_name,
            last_name=bet.last_name,
        )

    @classmethod
    def from_bytes(cls, data):
        offset = 0
        document = int.from_bytes(
            data[offset : offset + cls._DOCUMENT_BYTES], byteorder="big"
        )
        offset += cls._DOCUMENT_BYTES
        number = int.from_bytes(data[offset : offset + cls._NUMBER_BYTES], byteorder="big")
        offset += cls._NUMBER_BYTES
        birthdate = data[offset : offset + cls._BIRTHDATE_BYTES].decode("utf-8")
        offset += cls._BIRTHDATE_BYTES
        first_name_length = data[offset]
        offset += cls._NAME_LENGTH_BYTES
        first_name = data[offset : offset + first_name_length].decode("utf-8")
        offset += first_name_length
        last_name_length = data[offset]
        offset += cls._NAME_LENGTH_BYTES
        last_name = data[offset : offset + last_name_length].decode("utf-8")
        return cls(document, number, birthdate, first_name, last_name)

    def to_bytes(self):
        first_name_in_bytes = self._first_name.encode("utf-8")
        last_name_in_bytes = self._last_name.encode("utf-8")
        return (
            self._document.to_bytes(self._DOCUMENT_BYTES, byteorder="big")
            + self._number.to_bytes(self._NUMBER_BYTES, byteorder="big")
            + self._birthdate.encode("utf-8")
            + len(first_name_in_bytes).to_bytes(self._NAME_LENGTH_BYTES, byteorder="big")
            + first_name_in_bytes
            + len(last_name_in_bytes).to_bytes(self._NAME_LENGTH_BYTES, byteorder="big")
            + last_name_in_bytes
        )

    def to_bet(self, agency_id: int) -> Bet:
        return Bet(
            agency_id=agency_id,
            first_name=self._first_name,
            last_name=self._last_name,
            document=self._document,
            birthdate=self._birthdate,
            number=self._number,
        )
