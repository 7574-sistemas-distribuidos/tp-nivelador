import unittest

from protocol.message import (
    StartBetWinnersSendingMessage,
    BetWinnerMessage,
    FinalizeBetWinnersSendingMessage,
    StartBetsSendingMessage,
)
from lottery.bet import Bet


class StartBetWinnersSendingMessageTests(unittest.TestCase):
    START_BET_WINNERS_SENDING_TYPE = b"\x04"
    ZERO_LENGTH = b"\x00\x00"
    EMPTY_PAYLOAD = b""

    def test_it_serializes_to_its_type_followed_by_a_zero_length_payload(self):
        message = StartBetWinnersSendingMessage()

        self.assertEqual(
            message.to_bytes(),
            self.START_BET_WINNERS_SENDING_TYPE + self.ZERO_LENGTH + self.EMPTY_PAYLOAD,
        )


class BetWinnerMessageTests(unittest.TestCase):
    BET_WINNER_TYPE = b"\x05"
    THIRTY_EIGHT_BYTE_PAYLOAD_LENGTH = b"\x00\x26"

    DOCUMENT_34407251 = b"\x02\x0d\x03\x53"
    NUMBER_1033 = b"\x04\x09"
    BIRTHDATE_2001_08_29 = b"2001-08-29"
    FIRST_NAME_LENGTH_14 = b"\x0e"
    FIRST_NAME_TIAGO_NICOLAS = b"Tiago Nicol\xc3\xa1s"
    LAST_NAME_LENGTH_6 = b"\x06"
    LAST_NAME_RIVERA = b"Rivera"

    def test_it_serializes_the_bet_fields_in_wire_order(self):
        winner_bet = Bet(
            agency_id=1,
            first_name="Tiago Nicolás",
            last_name="Rivera",
            document=34407251,
            birthdate="2001-08-29",
            number=1033,
        )

        message = BetWinnerMessage(winner_bet)

        self.assertEqual(
            message.to_bytes(),
            self.BET_WINNER_TYPE
            + self.THIRTY_EIGHT_BYTE_PAYLOAD_LENGTH
            + self.DOCUMENT_34407251
            + self.NUMBER_1033
            + self.BIRTHDATE_2001_08_29
            + self.FIRST_NAME_LENGTH_14
            + self.FIRST_NAME_TIAGO_NICOLAS
            + self.LAST_NAME_LENGTH_6
            + self.LAST_NAME_RIVERA,
        )

    def test_it_rejects_a_birthdate_shorter_than_ten_bytes(self):
        bet_with_unpadded_birthdate = Bet(
            agency_id=1,
            first_name="Tiago Nicolás",
            last_name="Rivera",
            document=34407251,
            birthdate="2001-8-29",
            number=1033,
        )

        message = BetWinnerMessage(bet_with_unpadded_birthdate)

        with self.assertRaises(ValueError):
            message.to_bytes()

    def test_it_rejects_a_ten_character_birthdate_that_is_eleven_bytes(self):
        bet_with_non_ascii_birthdate = Bet(
            agency_id=1,
            first_name="Tiago Nicolás",
            last_name="Rivera",
            document=34407251,
            birthdate="2001-08-2ñ",
            number=1033,
        )

        message = BetWinnerMessage(bet_with_non_ascii_birthdate)

        with self.assertRaises(ValueError):
            message.to_bytes()


class FinalizeBetWinnersSendingMessageTests(unittest.TestCase):
    FINALIZE_BET_WINNERS_SENDING_TYPE = b"\x06"
    ZERO_LENGTH = b"\x00\x00"
    EMPTY_PAYLOAD = b""

    def test_it_serializes_to_its_type_followed_by_a_zero_length_payload(self):
        message = FinalizeBetWinnersSendingMessage()

        self.assertEqual(
            message.to_bytes(),
            self.FINALIZE_BET_WINNERS_SENDING_TYPE
            + self.ZERO_LENGTH
            + self.EMPTY_PAYLOAD,
        )


class StartBetsSendingMessageTests(unittest.TestCase):
    AGENCY_ID_1_PAYLOAD = b"\x01"

    def test_it_parses_the_agency_id_from_a_single_byte_payload(self):
        message = StartBetsSendingMessage.from_bytes(self.AGENCY_ID_1_PAYLOAD)

        self.assertEqual(message.agency_id(), 1)


if __name__ == "__main__":
    unittest.main()
