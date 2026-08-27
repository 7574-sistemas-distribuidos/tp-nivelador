package safe_socket

import "io"

//TODO: Complete with a short-read/short-write tolerant implementation

func SendAll(socket io.Writer, bytes []byte) error {
	bytesToSend := len(bytes)
	bytesSent := 0

	for bytesSent < bytesToSend {
		n, err := socket.Write(bytes[bytesSent:])
		if err != nil {
			return err
		}
		bytesSent += n
	}
	return nil
}

func RecvAll(socket io.Reader, size int) ([]byte, error) {
	buff := make([]byte, size)
	bytesReceived := 0
	for bytesReceived < size {
		n, err := socket.Read(buff[bytesReceived:])
		if err != nil {
			return nil, err
		}
		bytesReceived += n
	}
	return buff, nil
}
