import socket


def recv_all(sock: socket.socket, size: int) -> bytes:
    buffer = bytearray()
    while len(buffer) < size:
        chunk = sock.recv(size - len(buffer))
        if not chunk:
            raise ConnectionError(
                f"socket connection broken while receiving: "
                f"expected {size} bytes, got {len(buffer)}"
            )
        buffer.extend(chunk)
    return bytes(buffer)


def send_all(sock: socket.socket, data: bytes) -> None:
    view = memoryview(data)
    total = len(view)
    sent = 0
    while sent < total:
        n = sock.send(view[sent:])
        if n == 0:
            raise ConnectionError(
                f"socket connection broken while sending: "
                f"sent {sent} of {total} bytes"
            )
        sent += n
