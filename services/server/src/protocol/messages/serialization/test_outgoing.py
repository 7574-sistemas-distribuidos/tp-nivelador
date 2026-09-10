from lottery.bet import Bet
from protocol.messages.serialization.outgoing import (
    BetWinnerMessage,
    FinalizeBetWinnersSendingMessage,
    StartBetWinnersSendingMessage,
)


import unittest


class BetWinnerMessageTests(unittest.TestCase):
    BET_WINNER_TYPE = b"\x05"

    DOCUMENT_34407251 = b"\x02\x0d\x03\x53"
    NUMBER_1033 = b"\x00\x00\x04\x09"
    BIRTHDATE_2001_08_29 = b"2001-08-29"
    FIRST_NAME_LENGTH_14 = b"\x0e"
    FIRST_NAME_TIAGO_NICOLAS = b"Tiago Nicol\xc3\xa1s"
    LAST_NAME_LENGTH_6 = b"\x06"
    LAST_NAME_RIVERA = b"Rivera"

    WINNER_BET = Bet(
        agency_id=1,
        first_name="Tiago Nicolás",
        last_name="Rivera",
        document=34407251,
        birthdate="2001-08-29",
        number=1033,
    )

    def test_it_identifies_itself_with_the_bet_winner_type(self):
        message = BetWinnerMessage(self.WINNER_BET)

        self.assertEqual(message.type(), self.BET_WINNER_TYPE)

    def test_it_serializes_the_bet_fields_in_wire_order(self):
        message = BetWinnerMessage(self.WINNER_BET)

        self.assertEqual(
            message.payload(),
            self.DOCUMENT_34407251
            + self.NUMBER_1033
            + self.BIRTHDATE_2001_08_29
            + self.FIRST_NAME_LENGTH_14
            + self.FIRST_NAME_TIAGO_NICOLAS
            + self.LAST_NAME_LENGTH_6
            + self.LAST_NAME_RIVERA,
        )


class FinalizeBetWinnersSendingMessageTests(unittest.TestCase):
    FINALIZE_BET_WINNERS_SENDING_TYPE = b"\x06"
    EMPTY_PAYLOAD = b""

    def test_it_identifies_itself_with_the_finalize_bet_winners_sending_type(self):
        message = FinalizeBetWinnersSendingMessage()

        self.assertEqual(message.type(), self.FINALIZE_BET_WINNERS_SENDING_TYPE)

    def test_it_carries_no_payload(self):
        message = FinalizeBetWinnersSendingMessage()

        self.assertEqual(message.payload(), self.EMPTY_PAYLOAD)


class StartBetWinnersSendingMessageTests(unittest.TestCase):
    START_BET_WINNERS_SENDING_TYPE = b"\x04"
    EMPTY_PAYLOAD = b""

    def test_it_identifies_itself_with_the_start_bet_winners_sending_type(self):
        message = StartBetWinnersSendingMessage()

        self.assertEqual(message.type(), self.START_BET_WINNERS_SENDING_TYPE)

    def test_it_carries_no_payload(self):
        message = StartBetWinnersSendingMessage()

        self.assertEqual(message.payload(), self.EMPTY_PAYLOAD)
