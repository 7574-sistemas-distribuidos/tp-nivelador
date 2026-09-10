from protocol.messages.bet_record import BetRecord
from protocol.errors import ProtocolError


class StartBetsSendingMessage:
    _AGENCY_ID_BYTES = 1

    def __init__(self, agency_id: int):
        self._agency_id = agency_id

    @classmethod
    def from_bytes(cls, payload):
        if len(payload) != cls._AGENCY_ID_BYTES:
            raise ProtocolError(
                f"start_bets_sending payload must be exactly "
                f"{cls._AGENCY_ID_BYTES} byte, got {len(payload)}"
            )
        agency_id = int.from_bytes(payload, byteorder="big")
        return cls(agency_id)

    def agency_id(self):
        return self._agency_id


class FilledBetsMessage:
    def __init__(self, records: list[BetRecord]):
        self._bet_records = records

    @classmethod
    def from_bytes(cls, payload):
        if len(payload) == 0:
            raise ProtocolError("filled_bets carries no bet records")

        records = []
        offset = 0
        while offset < len(payload):
            record, offset = BetRecord.consume_from(payload, offset)
            records.append(record)
        return cls(records)

    def bets_for(self, agency_id: int):
        return [record.to_bet(agency_id) for record in self._bet_records]


class FinalizeBetsSendingMessage:
    @classmethod
    def from_bytes(cls, payload):
        if len(payload) != 0:
            raise ProtocolError(
                f"finalize_bets_sending carries no payload, got {len(payload)} bytes"
            )
        return cls()
