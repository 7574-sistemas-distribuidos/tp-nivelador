import unittest

from protocol.bet_record import BetRecord


class BetRecordTests(unittest.TestCase):
    def test_it_rejects_a_birthdate_shorter_than_ten_bytes(self):
        with self.assertRaises(ValueError):
            BetRecord(
                document=34407251,
                number=1033,
                birthdate="2001-8-29",
                first_name="Tiago Nicolás",
                last_name="Rivera",
            )

    def test_it_rejects_a_ten_character_birthdate_that_is_eleven_bytes(self):
        with self.assertRaises(ValueError):
            BetRecord(
                document=34407251,
                number=1033,
                birthdate="2001-08-2ñ",
                first_name="Tiago Nicolás",
                last_name="Rivera",
            )


if __name__ == "__main__":
    unittest.main()
