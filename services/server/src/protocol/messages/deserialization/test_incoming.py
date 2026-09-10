from lottery.bet import Bet
from protocol.errors import ProtocolError
from protocol.messages.deserialization.incoming import FilledBetsMessage, FinalizeBetsSendingMessage, StartBetsSendingMessage


import unittest


class StartBetsSendingMessageTests(unittest.TestCase):
    AGENCY_ID_1_PAYLOAD = b"\x01"

    def test_it_parses_the_agency_id_from_a_single_byte_payload(self):
        message = StartBetsSendingMessage.from_bytes(self.AGENCY_ID_1_PAYLOAD)

        self.assertEqual(message.agency_id(), 1)

    def test_it_rejects_an_empty_payload(self):
        with self.assertRaises(ProtocolError):
            StartBetsSendingMessage.from_bytes(b"")

    def test_it_rejects_a_payload_longer_than_one_byte(self):
        with self.assertRaises(ProtocolError):
            StartBetsSendingMessage.from_bytes(b"\x01\x02")


class FinalizeBetsSendingMessageTests(unittest.TestCase):
    def test_it_rejects_a_payload_that_carries_anything(self):
        with self.assertRaises(ProtocolError):
            FinalizeBetsSendingMessage.from_bytes(b"\x00")


class FilledBetsMessageTests(unittest.TestCase):
    CONNECTION_AGENCY_ID = 1

    DOCUMENT_34407251 = b"\x02\x0d\x03\x53"
    NUMBER_1033 = b"\x04\x09"
    BIRTHDATE_2001_08_29 = b"2001-08-29"
    FIRST_NAME_LENGTH_14 = b"\x0e"
    FIRST_NAME_TIAGO_NICOLAS = b"Tiago Nicol\xc3\xa1s"
    LAST_NAME_LENGTH_6 = b"\x06"
    LAST_NAME_RIVERA = b"Rivera"

    BET_RECORD_PAYLOAD = (
        DOCUMENT_34407251
        + NUMBER_1033
        + BIRTHDATE_2001_08_29
        + FIRST_NAME_LENGTH_14
        + FIRST_NAME_TIAGO_NICOLAS
        + LAST_NAME_LENGTH_6
        + LAST_NAME_RIVERA
    )

    def test_it_parses_the_bet_fields_from_a_single_record_payload(self):
        message = FilledBetsMessage.from_bytes(self.BET_RECORD_PAYLOAD)

        self.assertEqual(
            message.bets_for(self.CONNECTION_AGENCY_ID)[0],
            Bet(
                agency_id=1,
                first_name="Tiago Nicolás",
                last_name="Rivera",
                document=34407251,
                birthdate="2001-08-29",
                number=1033,
            ),
        )

    SECOND_BET_RECORD_PAYLOAD = (
        b"\x00\x0f\x12\x06"
        + b"\x1d\x9a"
        + b"1999-03-17"
        + b"\x17"
        + b"Milagros De Los Angeles"
        + b"\x0a"
        + b"Valenzuela"
    )

    def test_it_parses_every_record_in_a_batch_payload(self):
        batch = self.BET_RECORD_PAYLOAD + self.SECOND_BET_RECORD_PAYLOAD

        message = FilledBetsMessage.from_bytes(batch)

        self.assertEqual(
            message.bets_for(self.CONNECTION_AGENCY_ID),
            [
                Bet(
                    agency_id=1,
                    first_name="Tiago Nicolás",
                    last_name="Rivera",
                    document=34407251,
                    birthdate="2001-08-29",
                    number=1033,
                ),
                Bet(
                    agency_id=1,
                    first_name="Milagros De Los Angeles",
                    last_name="Valenzuela",
                    document=987654,
                    birthdate="1999-03-17",
                    number=7578,
                ),
            ],
        )

    def test_it_rejects_a_batch_whose_last_record_is_truncated(self):
        truncated_batch = self.BET_RECORD_PAYLOAD + self.SECOND_BET_RECORD_PAYLOAD[:-4]

        with self.assertRaises(ProtocolError):
            FilledBetsMessage.from_bytes(truncated_batch)

    def test_it_rejects_a_batch_carrying_no_records(self):
        with self.assertRaises(ProtocolError):
            FilledBetsMessage.from_bytes(b"")


if __name__ == "__main__":
    unittest.main()
