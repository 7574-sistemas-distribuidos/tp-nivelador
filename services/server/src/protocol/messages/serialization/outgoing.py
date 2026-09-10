from lottery.bet import Bet
from protocol.messages.bet_record import BetRecord


class StartBetWinnersSendingMessage:
    def type(self):
        return b"\x04"

    def payload(self):
        return b""


class BetWinnerMessage:
    def __init__(self, bet: Bet):
        self._bet_record = BetRecord.from_bet(bet)

    def type(self):
        return b"\x05"

    def payload(self):
        return self._bet_record.to_bytes()


class FinalizeBetWinnersSendingMessage:
    def type(self):
        return b"\x06"

    def payload(self):
        return b""


class ProcessedBetsBatchMessage:
    def type(self):
        return b"\x07"

    def payload(self):
        return b""


class RejectedBetsBatchMessage:
    def type(self):
        return b"\x08"

    def payload(self):
        return b""
