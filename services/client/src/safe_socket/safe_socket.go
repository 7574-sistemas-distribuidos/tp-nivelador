package safe_socket

import "io"

//TODO: Complete with a short-read/short-write tolerant implementation

func SendAll(socket io.Writer, bytes []byte) error {
	_, err := socket.Write(bytes)
	if err != nil {
		return err
	}
	return nil
}

func RecvAll(socket io.Reader, size int) ([]byte, error) {
	buff := make([]byte, size)
	n, err := socket.Read(buff)
	if err != nil {
		return nil, err
	}
	return buff[:n], nil
}
