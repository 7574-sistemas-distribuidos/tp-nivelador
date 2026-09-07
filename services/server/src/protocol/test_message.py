import unittest

from protocol.message import StartBetWinnersSendingMessage

START_BET_WINNERS_SENDING_TYPE = b"\x04"
ZERO_LENGTH = b"\x00\x00"
EMPTY_PAYLOAD = b""

class StartBetWinnersSendingMessageTests(unittest.TestCase):
    def test_it_serializes_to_its_type_followed_by_a_zero_length_payload(self):
        message = StartBetWinnersSendingMessage()

        self.assertEqual(
            message.to_bytes(),
            START_BET_WINNERS_SENDING_TYPE + ZERO_LENGTH + EMPTY_PAYLOAD)


if __name__ == "__main__":
    unittest.main()
