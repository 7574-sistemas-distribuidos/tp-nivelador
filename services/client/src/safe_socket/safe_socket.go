package safe_socket

import "io"

func SendAll(socket io.Writer, bytes []byte) error {
	for sent := 0; sent < len(bytes); {
		n, err := socket.Write(bytes[sent:])

		if err != nil {
			return err
		}
		sent += n
	}
	return nil
}

func RecvAll(socket io.Reader, size int) ([]byte, error) {
	buff := make([]byte, size)

	for recv := 0; recv < size; {
		n, err := socket.Read(buff[recv:])

		if err != nil {
			return buff[:recv], err
		}
		recv += n
	}
	return buff[:n], nil
}
