package safe_socket

import "io"

// SendAll writes the entire byte slice into the socket, handling short writes.
func SendAll(socket io.Writer, bytes []byte) error {
	totalSent := 0
	for totalSent < len(bytes) {
		n, err := socket.Write(bytes[totalSent:])
		if err != nil {
			return err
		}
		totalSent += n
	}
	return nil
}

// RecvAll reads exactly size bytes from the socket, handling short reads.
func RecvAll(socket io.Reader, size int) ([]byte, error) {
	buff := make([]byte, size)
	totalRead := 0
	for totalRead < size {
		n, err := socket.Read(buff[totalRead:])
		if n > 0 {
			totalRead += n
		}
		if err != nil {
			return buff[:totalRead], err
		}
	}
	return buff[:totalRead], nil
}
