package safe_socket

import "io"
import "errors"

// Short-read/short-write tolerant implementation

func SendAll(socket io.Writer, bytes []byte) error {
    total_bytes_sent := 0
	for total_bytes_sent < len(bytes) {
		n, err := socket.Write(bytes[total_bytes_sent:])
		if err != nil {
			return err
		}
		if n == 0 {
			return errors.New("Error de conexion dureante el envio de datos")
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
		if n == 0 {
			return nil, errors.New("Error de conexion durante la recepcion de datos")
		}
		total_bytes_received += n
	}
	return buffer, nil
}