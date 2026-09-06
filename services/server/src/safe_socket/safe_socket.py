import socket

# TODO: Complete with a short-read/short-write tolerant implementation


def recv_all(socket: socket.socket, totalBytesToReceive):
    bytes_counter = 0
    received_byte_data = socket.recv(totalBytesToReceive)

    if received_byte_data == b"":
        raise ConnectionError("Socket closed before receiving all data")

    bytes_counter += len(received_byte_data)
    
    if bytes_counter == totalBytesToReceive:
        return received_byte_data
       
    while bytes_counter < totalBytesToReceive:
        remaining_bytes_to_receive = totalBytesToReceive - bytes_counter
        new_received_data = socket.recv(remaining_bytes_to_receive)

        if new_received_data == b"":
            raise ConnectionError("Socket closed before receiving all data")

        received_byte_data += new_received_data
        bytes_counter += len(new_received_data)


    return received_byte_data


def send_all(socket: socket.socket, bytes):
    return socket.send(bytes)
