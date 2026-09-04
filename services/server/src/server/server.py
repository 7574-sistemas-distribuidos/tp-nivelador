import socket
import logger
from domain.message import Message
from domain.message_header import MessageHeader, MessageType
import protocol
from domain.parser import parse_bet


class Server:
    def __init__(self, server_host: str, server_port: int) -> None:
        self.server_host = server_host
        self.server_port = server_port

    def _handle_client(self, client_socket: socket.socket) -> None:
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
            case MessageType.REGISTER_AGENCY:
                self._handle_register_agency(client_socket)
            case MessageType.BET:
                self._handle_bet(client_socket, payload)
            case MessageType.AWAITING_WINNERS:
                self._handle_awaiting_winners(client_socket, payload)
            case _:
                raise ValueError(f"unexpected message type: {header.type}")


    def _handle_register_agency(self, client_socket: socket.socket) -> None:

        protocol.send_message(client_socket, Message.ack())

    def _handle_bet(self, client_socket: socket.socket, payload: bytes) -> None:
        bet = parse_bet(payload)

        protocol.send_message(client_socket, Message.ack())

    def _handle_awaiting_winners(self, client_socket: socket.socket, payload: bytes) -> None:
        # TODO: marcar que esta agencia está esperando ganadores
        # (el envío real de MessageTypeWinner queda para después)
        pass

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
                    self._handle_client(client_socket)
                except Exception as e:
                    # Un cliente que falla no debe tumbar el servidor:
                    # el detalle ya se logueo en _handle_client, seguimos aceptando.
                    logger.error(
                        "drop-client-connection", logger.LogResult.fail, "err", e
                    )
