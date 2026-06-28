import logging
import socket

_ECHO_SERVER_MESSAGE_SIZE = 1024


class Server:
    def __init__(self, server_host: str, server_port: str) -> None:
        self.server_host = server_host
        self.server_port = server_port

    def _handle_client(self, client_socket):
        while True:
            client_message = client_socket.recv(_ECHO_SERVER_MESSAGE_SIZE)
            if not client_message:
                logging.info("Client disconnected")
                return

            logging.info(f"Echoing to client {client_message.decode('utf-8')}")
            client_socket.sendall(client_message)

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.server_host, self.server_port))
            server_socket.listen()
            while True:
                logging.info("Listening to connections")
                client_socket, _ = server_socket.accept()

                logging.info("A new client has connected")
                self._handle_client(client_socket)
