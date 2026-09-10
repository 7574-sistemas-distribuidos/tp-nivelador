package safe_socket

import "io"

// Short-read/short-write tolerant implementation

func SendAll(socket io.Writer, bytes []byte) error {
    total_bytes_sent := 0
	for total_bytes_sent < len(bytes) {
		n, err := socket.Write(bytes[total_bytes_sent:])
		if err != nil {
			return err
		}
		total_bytes_sent += n
	}
	return nil
}

func RecvAll(socket io.Reader, size int) ([]byte, error) {
	buffer := make([]byte, size)
	total_bytes_received := 0
	for total_bytes_received < size {
		n, err := socket.Read(buffer[total_bytes_received:])
		if err != nil {
			return nil, err
		}
		total_bytes_received += n
	}
	return buffer, nil
}