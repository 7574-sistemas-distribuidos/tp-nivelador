import unittest

from protocol.channel import MessageChannel
from protocol.errors import ProtocolError
from protocol.messages.serialization.outgoing import (
    BetWinnerMessage,
    FinalizeBetWinnersSendingMessage,
)
from lottery.bet import Bet
from protocol.messages.deserialization.incoming import FilledBetMessage, FinalizeBetsSendingMessage, StartBetsSendingMessage


class FakeSocket:
    def __init__(self, data, max_chunk=None):
        self._data = data
        self._position = 0
        self._max_chunk = max_chunk
        self.sent = b""

    def recv(self, size):
        if self._max_chunk is not None:
            size = min(size, self._max_chunk)
        chunk = self._data[self._position : self._position + size]
        self._position += len(chunk)
        return chunk

    def send(self, data):
        if self._max_chunk is not None:
            data = data[: self._max_chunk]
        self.sent += data
        return len(data)


class MessageChannelReceiveTests(unittest.TestCase):
    START_BETS_SENDING_TYPE = b"\x01"
    ONE_BYTE_LENGTH = b"\x00\x01"
    AGENCY_ID_1_PAYLOAD = b"\x01"

    START_BETS_SENDING_FRAME = (
        START_BETS_SENDING_TYPE + ONE_BYTE_LENGTH + AGENCY_ID_1_PAYLOAD
    )

    def test_it_receives_a_start_bets_sending_message(self):
        socket_with_start_bets_sending_message = FakeSocket(self.START_BETS_SENDING_FRAME)
        channel = MessageChannel(socket_with_start_bets_sending_message)

        message = channel.receive()

        self.assertIsInstance(message, StartBetsSendingMessage)
        self.assertEqual(message.agency_id(), 1)

    def test_it_receives_a_message_delivered_one_byte_per_read(self):
        socket_with_start_bets_sending_message = FakeSocket(self.START_BETS_SENDING_FRAME, max_chunk=1)
        channel = MessageChannel(socket_with_start_bets_sending_message)

        message = channel.receive()

        self.assertEqual(message.agency_id(), 1)


    FINALIZE_BETS_SENDING_TYPE = b"\x03"
    ZERO_LENGTH = b"\x00\x00"

    FINALIZE_BETS_SENDING_FRAME = FINALIZE_BETS_SENDING_TYPE + ZERO_LENGTH

    def test_it_receives_a_finalize_bets_sending_message_with_no_payload(self):
        socket_with_finalize_bets_sending_message = FakeSocket(self.FINALIZE_BETS_SENDING_FRAME)
        channel = MessageChannel(socket_with_finalize_bets_sending_message)

        message = channel.receive()

        self.assertIsInstance(message, FinalizeBetsSendingMessage)


    UNKNOWN_TYPE = b"\x7f"

    UNKNOWN_TYPE_FRAME = UNKNOWN_TYPE + ZERO_LENGTH

    def test_it_rejects_a_frame_carrying_an_unknown_message_type(self):
        socket_with_unknown_type_frame = FakeSocket(self.UNKNOWN_TYPE_FRAME)
        channel = MessageChannel(socket_with_unknown_type_frame)

        with self.assertRaises(ProtocolError):
            channel.receive()


    FILLED_BET_TYPE = b"\x02"
    THIRTY_EIGHT_BYTE_LENGTH = b"\x00\x26"
    BET_RECORD_PAYLOAD = (
        b"\x02\x0d\x03\x53"
        + b"\x04\x09"
        + b"2001-08-29"
        + b"\x0e"
        + b"Tiago Nicol\xc3\xa1s"
        + b"\x06"
        + b"Rivera"
    )

    FILLED_BET_FRAME = FILLED_BET_TYPE + THIRTY_EIGHT_BYTE_LENGTH + BET_RECORD_PAYLOAD

    CONNECTION_AGENCY_ID = 1

    def test_it_receives_a_filled_bet_message(self):
        socket_with_filled_bet_message = FakeSocket(self.FILLED_BET_FRAME)
        channel = MessageChannel(socket_with_filled_bet_message)

        message = channel.receive()

        self.assertIsInstance(message, FilledBetMessage)
        self.assertEqual(
            message.bet_for(self.CONNECTION_AGENCY_ID),
            Bet(
                agency_id=1,
                first_name="Tiago Nicolás",
                last_name="Rivera",
                document=34407251,
                birthdate="2001-08-29",
                number=1033,
            ),
        )


class MessageChannelSendTests(unittest.TestCase):
    FINALIZE_BET_WINNERS_SENDING_FRAME = b"\x06" + b"\x00\x00"

    BET_WINNER_FRAME = (
        b"\x05"
        + b"\x00\x26"
        + b"\x02\x0d\x03\x53"
        + b"\x04\x09"
        + b"2001-08-29"
        + b"\x0e"
        + b"Tiago Nicol\xc3\xa1s"
        + b"\x06"
        + b"Rivera"
    )

    WINNER_BET = Bet(
        agency_id=1,
        first_name="Tiago Nicol\u00e1s",
        last_name="Rivera",
        document=34407251,
        birthdate="2001-08-29",
        number=1033,
    )

    def test_it_frames_a_message_with_the_byte_count_of_its_payload(self):
        client_socket = FakeSocket(b"")
        channel = MessageChannel(client_socket)

        channel.send(BetWinnerMessage(self.WINNER_BET))

        self.assertEqual(client_socket.sent, self.BET_WINNER_FRAME)

    def test_it_sends_the_serialized_message(self):
        client_socket = FakeSocket(b"")
        channel = MessageChannel(client_socket)

        channel.send(FinalizeBetWinnersSendingMessage())

        self.assertEqual(client_socket.sent, self.FINALIZE_BET_WINNERS_SENDING_FRAME)

    def test_it_sends_a_message_one_byte_per_write(self):
        client_socket = FakeSocket(b"", max_chunk=1)
        channel = MessageChannel(client_socket)

        channel.send(FinalizeBetWinnersSendingMessage())

        self.assertEqual(client_socket.sent, self.FINALIZE_BET_WINNERS_SENDING_FRAME)


if __name__ == "__main__":
    unittest.main()
