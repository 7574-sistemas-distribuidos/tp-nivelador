package safe_socket

import (
	"net"
)

//TODO: Complete with a short-read/short-write tolerant implementation

func SendAll(socket net.Conn, bytes []byte) error {
	_, err := socket.Write(bytes)
	if err != nil {
		return err
	}
	return nil
}

func RecvAll(socket net.Conn, size int) ([]byte, error) {
	buff := make([]byte, size)
	_, err := socket.Read(buff)
	if err != nil {
		return nil, err
	}
	return buff, nil
}
