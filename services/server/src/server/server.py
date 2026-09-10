import socket
import threading


import logger
from lottery.lottery import Lottery
from protocol.channel import MessageChannel
from protocol.errors import ProtocolError
from protocol.messages.deserialization.incoming import (
    FilledBetsMessage,
    FinalizeBetsSendingMessage,
    StartBetsSendingMessage,
)
from protocol.messages.serialization.outgoing import (
    BetWinnerMessage,
    FinalizeBetWinnersSendingMessage,
    ProcessedBetsBatchMessage,
    RejectedBetsBatchMessage,
    StartBetWinnersSendingMessage,
)

_BETS_STORAGE_PATH = "bets.csv"


class Server:
    def __init__(
        self, server_host: str, server_port: int, agency_quorum_min: int
    ) -> None:
        self._server_host = server_host
        self._server_port = server_port
        self._agency_quorum_min = agency_quorum_min
        self._lottery = Lottery(_BETS_STORAGE_PATH)
        self._threads = []

    def _handle_client(self, client_socket):
        action = "handle-client"
        ## TODO: Refactor to remove ifs that are being the state machine of the protocol.
        ## Code below represents an AgencySession, think of a double dispatch.
        with client_socket:
            message_channel = MessageChannel(client_socket)
            start_bets_sending = message_channel.receive()
            if not isinstance(start_bets_sending, StartBetsSendingMessage):
                raise ProtocolError(
                    f"expected a start_bets_sending, got {type(start_bets_sending).__name__}"
                )

            agency_id = start_bets_sending.agency_id()

            while True:
                try:
                    message = message_channel.receive()
                    if isinstance(message, FinalizeBetsSendingMessage):
                        break
                    if not isinstance(message, FilledBetsMessage):
                        raise ProtocolError(
                            f"expected a filled_bets or a finalize_bets_sending, "
                            f"got {type(message).__name__}"
                        )
                    bets = message.bets_for(agency_id)
                    self._lottery.store_bets(bets)
                    logger.info(
                        action,
                        logger.LogResult.success,
                        "bets-in-batch",
                        len(bets),
                    )
                except ProtocolError:
                    message_channel.send(RejectedBetsBatchMessage())
                    raise

                message_channel.send(ProcessedBetsBatchMessage())

            message_channel.send(StartBetWinnersSendingMessage())
            for bet in self._lottery.load_bets():
                if bet.agency_id == agency_id and self._lottery.has_won(bet):
                    message_channel.send(BetWinnerMessage(bet))
            message_channel.send(FinalizeBetWinnersSendingMessage())

    def _run_session(self, client_socket):
        action = "handle-client"
        try:
            self._handle_client(client_socket)
        except (ConnectionError, ProtocolError) as e:
            logger.error(action, logger.LogResult.fail, "err", e)
        except Exception as e:
            logger.error(action, logger.LogResult.fail, "err", e)
            raise

    def run(self):
        accept_action = "accept-connection"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self._server_host, self._server_port))
            server_socket.listen()
            while True:
                try:
                    logger.info(accept_action, logger.LogResult.in_progress)
                    client_socket, _ = server_socket.accept()
                    client_thread = threading.Thread(
                        target=self._run_session, args=(client_socket,)
                    )
                    self._threads.append(client_thread)
                    client_thread.start()
                except Exception as e:
                    logger.error(accept_action, logger.LogResult.fail)
                    raise e
                logger.info(accept_action, logger.LogResult.success)
