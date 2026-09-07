import unittest

from protocol.bet_record import BetRecord
from protocol.errors import ProtocolError


class BetRecordTests(unittest.TestCase):
    VALID_RECORD_BYTES = (
        b"\x02\x0d\x03\x53"
        + b"\x04\x09"
        + b"2001-08-29"
        + b"\x0e"
        + b"Tiago Nicol\xc3\xa1s"
        + b"\x06"
        + b"Rivera"
    )

    def test_it_rejects_a_payload_too_short_to_hold_the_fixed_fields(self):
        truncated = self.VALID_RECORD_BYTES[:12]

        with self.assertRaises(ProtocolError):
            BetRecord.from_bytes(truncated)

    def test_it_rejects_a_first_name_length_that_overruns_the_record(self):
        overrun = (
            self.VALID_RECORD_BYTES[:16]
            + bytes([200])
            + self.VALID_RECORD_BYTES[17:]
        )

        with self.assertRaises(ProtocolError):
            BetRecord.from_bytes(overrun)

    def test_it_rejects_a_record_with_trailing_bytes(self):
        with_trailing_junk = self.VALID_RECORD_BYTES + b"XXXX"

        with self.assertRaises(ProtocolError):
            BetRecord.from_bytes(with_trailing_junk)

    def test_it_rejects_a_name_that_is_not_valid_utf_8(self):
        lone_continuation_byte = b"\xff\xfe"
        invalid_utf_8 = (
            self.VALID_RECORD_BYTES[:16]
            + bytes([len(lone_continuation_byte)])
            + lone_continuation_byte
            + b"\x06"
            + b"Rivera"
        )

        with self.assertRaises(ProtocolError):
            BetRecord.from_bytes(invalid_utf_8)

    def test_it_rejects_a_birthdate_shorter_than_ten_bytes(self):
        with self.assertRaises(ProtocolError):
            BetRecord(
                document=34407251,
                number=1033,
                birthdate="2001-8-29",
                first_name="Tiago Nicolás",
                last_name="Rivera",
            )

    def test_it_rejects_a_ten_character_birthdate_that_is_eleven_bytes(self):
        with self.assertRaises(ProtocolError):
            BetRecord(
                document=34407251,
                number=1033,
                birthdate="2001-08-2ñ",
                first_name="Tiago Nicolás",
                last_name="Rivera",
            )


if __name__ == "__main__":
    unittest.main()
