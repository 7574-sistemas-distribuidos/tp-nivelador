from lottery.bet import Bet


class StartBetWinnersSendingMessage:
    def to_bytes(self):
        return self._type() + self._length() + self._payload()

    def _type(self):
        return b"\x04"

    def _length(self):
        payload_length = len(self._payload())
        return payload_length.to_bytes(2, byteorder="big")

    def _payload(self):
        return b""


class BetWinnerMessage:
    _BIRTHDATE_BYTES = 10
    def __init__(self, bet: Bet):
        self._bet = bet

    def to_bytes(self):
        return self._type() + self._length() + self._payload()

    def _type(self):
        return b"\x05"

    def _length(self):
        payload_length = len(self._payload())
        return payload_length.to_bytes(2, byteorder="big")

    def _payload(self):
        document_in_bytes = self._bet.document.to_bytes(4, byteorder="big")
        number_in_bytes = self._bet.number.to_bytes(2, byteorder="big")
        birthdate_in_bytes = self._bet.birthdate.encode("utf-8")
        if len(birthdate_in_bytes) != self._BIRTHDATE_BYTES:
            raise ValueError(
                f"birthdate must be exactly {self._BIRTHDATE_BYTES} bytes, "
                f"got {len(birthdate_in_bytes)}: {self._bet.birthdate!r}"
            )
        first_name_in_bytes = self._bet.first_name.encode("utf-8")
        last_name_in_bytes = self._bet.last_name.encode("utf-8")
        return (
            document_in_bytes
            + number_in_bytes
            + birthdate_in_bytes
            + len(first_name_in_bytes).to_bytes(1, byteorder="big")
            + first_name_in_bytes
            + len(last_name_in_bytes).to_bytes(1, byteorder="big")
            + last_name_in_bytes
        )
