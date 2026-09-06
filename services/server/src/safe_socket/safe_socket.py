import socket


def recv_all(socket: socket.socket, total_bytes_to_receive):
    bytes_counter = 0
    received_byte_data = socket.recv(total_bytes_to_receive)

    if received_byte_data == b"":
        raise ConnectionError("Socket closed before receiving all data")

    bytes_counter += len(received_byte_data)

    if bytes_counter == total_bytes_to_receive:
        return received_byte_data

    while bytes_counter < total_bytes_to_receive:
        remaining_bytes_to_receive = total_bytes_to_receive - bytes_counter
        new_received_data = socket.recv(remaining_bytes_to_receive)

        if new_received_data == b"":
            raise ConnectionError("Socket closed before receiving all data")

        received_byte_data += new_received_data
        bytes_counter += len(new_received_data)

    return received_byte_data


def send_all(socket: socket.socket, byte_data):
    bytes_counter = 0
    total_bytes_to_send = len(byte_data)
    bytes_sent = socket.send(byte_data)

    bytes_counter += bytes_sent

    if bytes_counter == total_bytes_to_send:
        return bytes_sent

    while bytes_counter < total_bytes_to_send:
        remaining_byte_data_to_send = byte_data[bytes_counter:]
        bytes_sent = socket.send(remaining_byte_data_to_send)
        bytes_counter += bytes_sent

    return bytes_counter
