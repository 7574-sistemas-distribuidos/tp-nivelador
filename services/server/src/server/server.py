import os
import socket

import logger
import lottery
from domain.message import Message
from domain.message_header import MessageHeader, MessageType
import protocol
from domain.parser import parse_agency_id, parse_bet
from lottery import Lottery

BETS_FILE_NAME = "bets.csv"


class Server:
    def __init__(self, server_host: str, server_port: int, storage_dir: str) -> None:
        self.server_host = server_host
        self.server_port = server_port
        self.lottery = Lottery(os.path.join(storage_dir, BETS_FILE_NAME))

    def _handle_agency_connection(self, client_socket: socket.socket) -> None:
        action = "handle-client"
        message_amount = 0

        try:
            logger.info(action, logger.LogResult.in_progress)
            with client_socket:
                while True:
                    header, payload = protocol.receive_message(client_socket)
                    message_amount += 1
                    self._dispatch(client_socket, header, payload)
                    if header.type == MessageType.AWAITING_WINNERS:
                        break
            logger.info(
                action, logger.LogResult.success, "messages-amount", message_amount
            )
        except Exception as e:
            logger.error(
                action, logger.LogResult.fail, "messages-amount", message_amount
            )
            raise e

    def _dispatch(self, client_socket: socket.socket, header: MessageHeader, payload: bytes) -> None:
        match header.type:
            case MessageType.BET:
                self._handle_bet(client_socket, payload)
            case MessageType.AWAITING_WINNERS:
                self._handle_awaiting_winners(client_socket, payload)
            case _:
                raise ValueError(f"unexpected message type: {header.type}")


    def _handle_bet(self, client_socket: socket.socket, payload: bytes) -> None:
        bet = parse_bet(payload)
        self.lottery.store_bets([bet])
        protocol.send_message(client_socket, Message.ack())

    def _receive_ack(self, client_socket: socket.socket) -> None:
        header, _ = protocol.receive_message(client_socket)
        if header.type != MessageType.ACK:
            raise ValueError(f"expected ack message type, got {header.type}")

    def _handle_awaiting_winners(self, client_socket: socket.socket, payload: bytes) -> None:
        action = "send-winners"
        agency_id = parse_agency_id(payload)
        winners_amount = 0

        logger.info(action, logger.LogResult.in_progress, "agency-id", agency_id)
        protocol.send_message(client_socket, Message.ack())

        for bet in self.lottery.load_bets():
            if self.lottery.has_won(bet) and bet.agency_id == agency_id:
                protocol.send_message(client_socket, Message.winner(bet))
                self._receive_ack(client_socket)
                winners_amount += 1

        protocol.send_message(client_socket, Message.finish())
        self._receive_ack(client_socket)
        logger.info(
            action,
            logger.LogResult.success,
            "agency-id",
            agency_id,
            "winners-amount",
            winners_amount,
        )


    def run(self) -> None:
        action = "accept-connection"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.server_host, self.server_port))
            server_socket.listen()
            while True:
                try:
                    logger.info(action, logger.LogResult.in_progress)
                    client_socket, _ = server_socket.accept()
                except Exception:
                    logger.error(action, logger.LogResult.fail)
                    raise
                logger.info(action, logger.LogResult.success)
                try:
                    self._handle_agency_connection(client_socket)
                except Exception as e:
                    logger.error(
                        "drop-client-connection", logger.LogResult.fail, "err", e
                    )
