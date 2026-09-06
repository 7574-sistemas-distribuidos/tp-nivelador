package safe_socket

import (
	"fmt"
	"io"
)

//TODO: Complete with a short-read/short-write tolerant implementation

func SendAll(socket io.Writer, bytes []byte) error {
	_, err := socket.Write(bytes)
	if err != nil {
		return err
	}
	return nil
}

func RecvAll(socket io.Reader, totalBytesToReceive int) ([]byte, error) {
	fixedBuffer := make([]byte, totalBytesToReceive)
	positionsFilled := 0

	for positionsFilled < totalBytesToReceive {
		positionsJustFilled, err := socket.Read(fixedBuffer[positionsFilled:])
		positionsFilled += positionsJustFilled

		if err != nil && positionsFilled < totalBytesToReceive {
			return nil, fmt.Errorf("error while reading from socket: %w", err)
		}
	}

	return fixedBuffer, nil
}
