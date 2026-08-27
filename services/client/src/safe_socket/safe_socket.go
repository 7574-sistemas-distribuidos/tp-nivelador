package safe_socket

import "io"

func SendAll(socket io.Writer, bytes []byte) error {
	n, err := socket.Write(bytes)
	if err != nil {
		return err
	}
	for n < len(bytes) {
		bytes = bytes[n:]
		n, err = socket.Write(bytes)
		if err != nil {
			return err
		}
	}
	return nil
}

func RecvAll(socket io.Reader, size int) ([]byte, error) {
	buff := make([]byte, size)
	total := 0
	for total < size {
		n, err := socket.Read(buff[total:])
		if err != nil {
			return nil, err
		}
		total += n
	}
	return buff, nil
}
