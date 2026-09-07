from lottery.bet import Bet
from protocol.bet_record import BetRecord


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
    def __init__(self, bet: Bet):
        self._bet_record = BetRecord.from_bet(bet)

    def to_bytes(self):
        return self._type() + self._length() + self._payload()

    def _type(self):
        return b"\x05"

    def _length(self):
        payload_length = len(self._payload())
        return payload_length.to_bytes(2, byteorder="big")

    def _payload(self):
        return self._bet_record.to_bytes()


class FinalizeBetWinnersSendingMessage:
    def to_bytes(self):
        return self._type() + self._length() + self._payload()

    def _type(self):
        return b"\x06"

    def _length(self):
        payload_length = len(self._payload())
        return payload_length.to_bytes(2, byteorder="big")

    def _payload(self):
        return b""


class StartBetsSendingMessage:
    def __init__(self, agency_id: int):
        self._agency_id = agency_id

    @classmethod
    def from_bytes(cls, payload):
        agency_id = int.from_bytes(payload, byteorder="big")
        return cls(agency_id)

    def agency_id(self):
        return self._agency_id


class FilledBetMessage:
    def __init__(self, record: BetRecord):
        self._bet_record = record

    @classmethod
    def from_bytes(cls, payload):
        return cls(BetRecord.from_bytes(payload))

    def bet_for(self, agency_id: int):
        return self._bet_record.to_bet(agency_id)
