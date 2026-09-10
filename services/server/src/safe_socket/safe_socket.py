import socket


def send_all(sock: socket.socket, data: bytes) -> None:
    """Envía todos los bytes por el socket tolerando short writes."""
    total_sent = 0
    total_to_send = len(data)
    view = memoryview(data)
    while total_sent < total_to_send:
        sent = sock.send(view[total_sent:])
        total_sent += sent


def recv_all(sock: socket.socket, size: int) -> bytes:
    """Recibe exactamente size bytes del socket tolerando short reads.

    Si el socket se cierra al inicio (EOF), retorna b"".
    Si se corta en el medio de una lectura, lanza ConnectionError.
    """
    buffer = bytearray()
    while len(buffer) < size:
        chunk = sock.recv(size - len(buffer))
        if not chunk:
            if len(buffer) == 0:
                return b""
            raise ConnectionError(
                f"Connection closed prematurely: expected {size} bytes, got {len(buffer)}"
            )
        buffer.extend(chunk)
    return bytes(buffer)
