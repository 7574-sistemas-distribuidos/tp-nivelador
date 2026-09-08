import socket
import random

from .test_case import TestCase
from services.server.src.safe_socket import recv_all, send_all


class ChunkedSocket(socket.socket):
    def __init__(self, recv_buffer=b"", max_chunk_size=10):
        self.recv_buffer = recv_buffer
        self.send_buffer = b""
        self.max_chunk_size = max_chunk_size

    def recv(self, bufsize: int, _flags: int = 0) -> bytes:
        max_read_size = min(self.max_chunk_size, bufsize)
        if max_read_size <= 1:
            data_len_to_recv = 1
        else:
            data_len_to_recv = random.randrange(1, max_read_size)

        data_to_recv = self.recv_buffer[:data_len_to_recv]
        self.recv_buffer = self.recv_buffer[data_len_to_recv:]
        return data_to_recv

    def send(self, data, _flags: int = 0) -> int:
        data_len_to_send = (
            random.randrange(0, self.max_chunk_size) if self.max_chunk_size != 1 else 1
        )
        data_to_send = memoryview(data)[:data_len_to_send]
        self.send_buffer += bytes(data_to_send)
        return len(data_to_send)


class ServerShortReadWrite(TestCase):
    title = "server short read/write"
    error_hint = "I/O doesn't guarantee a full read/write in a single call"

    @staticmethod
    def _test_recv_all_case(bytes_to_recv: bytes, max_chunk_size: int):
        chunked_socket = ChunkedSocket(
            recv_buffer=bytes_to_recv, max_chunk_size=max_chunk_size
        )
        recv_bytes = recv_all(chunked_socket, len(bytes_to_recv))
        if bytes_to_recv != recv_bytes:
            raise ValueError(
                f"recv_all returned {len(recv_bytes)} of {len(bytes_to_recv)} sent bytes"
            )

    @staticmethod
    def _test_recv_all():
        ServerShortReadWrite._test_recv_all_case(b"hello-world", 4)
        ServerShortReadWrite._test_recv_all_case(b"Robert Smith,50000000,7574", 8)
        ServerShortReadWrite._test_recv_all_case(b"ack", 1)
        ServerShortReadWrite._test_recv_all_case(b"a" * 2048, 32)

    @staticmethod
    def _test_send_all_case(bytes_to_send: bytes, max_chunk_size: int):
        chunked_socket = ChunkedSocket(max_chunk_size=max_chunk_size)
        send_all(chunked_socket, bytes_to_send)
        sent_bytes = chunked_socket.send_buffer
        if bytes_to_send != sent_bytes:
            raise ValueError(
                f"send_all sent {len(sent_bytes)} of {len(bytes_to_send)} input bytes"
            )

    @staticmethod
    def _test_send_all():
        ServerShortReadWrite._test_send_all_case(b"hello-world", 4)
        ServerShortReadWrite._test_send_all_case(b"Robert Smith,50000000,7574", 8)
        ServerShortReadWrite._test_send_all_case(b"ack", 1)
        ServerShortReadWrite._test_send_all_case(b"a" * 2048, 32)

    @staticmethod
    def test() -> None:
        ServerShortReadWrite._test_recv_all()
        ServerShortReadWrite._test_send_all()
