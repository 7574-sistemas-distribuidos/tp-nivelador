from lottery.bet import Bet
from protocol.errors import ProtocolError


class BetRecord:
    _DOCUMENT_BYTES = 4
    _NUMBER_BYTES = 4
    _BIRTHDATE_BYTES = 10
    _NAME_LENGTH_BYTES = 1
    _FIXED_PREFIX_BYTES = _DOCUMENT_BYTES + _NUMBER_BYTES + _BIRTHDATE_BYTES

    def __init__(self, document, number, birthdate, first_name, last_name):
        birthdate_in_bytes = birthdate.encode("utf-8")
        if len(birthdate_in_bytes) != self._BIRTHDATE_BYTES:
            raise ProtocolError(
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
        record, consumed = cls.consume_from(data)
        if consumed != len(data):
            raise ProtocolError(
                f"bet record does not consume the payload exactly: "
                f"{len(data) - consumed} bytes remain"
            )
        return record

    @classmethod
    def consume_from(cls, data, offset=0):
        minimum = cls._FIXED_PREFIX_BYTES + 2 * cls._NAME_LENGTH_BYTES
        available = len(data) - offset
        if available < minimum:
            raise ProtocolError(
                f"bet record needs at least {minimum} bytes, got {available}"
            )

        document = int.from_bytes(
            data[offset : offset + cls._DOCUMENT_BYTES], byteorder="big"
        )
        offset += cls._DOCUMENT_BYTES
        number = int.from_bytes(data[offset : offset + cls._NUMBER_BYTES], byteorder="big")
        offset += cls._NUMBER_BYTES
        birthdate = cls._decoded(
            data[offset : offset + cls._BIRTHDATE_BYTES], "birthdate"
        )
        offset += cls._BIRTHDATE_BYTES
        first_name_length = data[offset]
        offset += cls._NAME_LENGTH_BYTES
        if offset + first_name_length + cls._NAME_LENGTH_BYTES > len(data):
            raise ProtocolError(
                f"first_name length {first_name_length} overruns the record: "
                f"only {len(data) - offset} bytes remain"
            )
        first_name = cls._decoded(
            data[offset : offset + first_name_length], "first_name"
        )
        offset += first_name_length
        last_name_length = data[offset]
        offset += cls._NAME_LENGTH_BYTES
        if offset + last_name_length > len(data):
            raise ProtocolError(
                f"last_name length {last_name_length} overruns the record: "
                f"only {len(data) - offset} bytes remain"
            )
        last_name = cls._decoded(
            data[offset : offset + last_name_length], "last_name"
        )
        offset += last_name_length
        return cls(document, number, birthdate, first_name, last_name), offset

    @classmethod
    def _decoded(cls, raw, field):
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ProtocolError(f"{field} is not valid utf-8") from e

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
