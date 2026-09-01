import socket
import logger
import safe_socket

LENGHT_MESSAGE_SIZE = 2


class Server:
    def __init__(self, server_host: str, server_port: int) -> None:
        self.server_host = server_host
        self.server_port = server_port

    def _handle_client(self, client_socket):
        action = "handle-client"
        message_amount = 0
        try:
            logger.info(action, logger.LogResult.in_progress)
            while True:
                
                client_message_size = safe_socket.recv_all(client_socket, LENGHT_MESSAGE_SIZE)
                if not client_message_size:
                    logger.info(
                        action,
                        logger.LogResult.success,
                        "messages-amount",
                        message_amount,
                    )
                    return
                
                message_size = int.from_bytes(client_message_size, byteorder='big')

                client_message = safe_socket.recv_all(
                    client_socket, message_size
                )
                if not client_message:
                    logger.info(
                        action,
                        logger.LogResult.success,
                        "messages-amount",
                        message_amount,
                    )
                    return
                message_amount += 1
                try:
                    safe_socket.send_all(client_socket, client_message_size)
                    safe_socket.send_all(client_socket, client_message)
                except RuntimeError as e:
                    logger.warn(action, "send failed, cliente desconectado", "messages-amount", message_amount)
                    return
                
        except Exception as e:
            logger.error(
                action, logger.LogResult.fail, "messages-amount", message_amount
            )
            return

    def run(self):
        action = "accept-connection"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.server_host, self.server_port))
            server_socket.listen()
            while True:
                try:
                    logger.info(action, logger.LogResult.in_progress)
                    client_socket, _ = server_socket.accept()
                except Exception as e:
                    logger.error(action, logger.LogResult.fail)
                    continue
                logger.info(action, logger.LogResult.success)

                self._handle_client(client_socket)
