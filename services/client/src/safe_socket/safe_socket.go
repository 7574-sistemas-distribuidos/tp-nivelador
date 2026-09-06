package safe_socket

import (
	"fmt"
	"io"
)

func SendAll(socket io.Writer, totalByteData []byte) error {
	writtenBytes := 0

	for writtenBytes < len(totalByteData) {
		writtenBytesNow, err := socket.Write(totalByteData[writtenBytes:])
		if err != nil {
			return err
		}
		writtenBytes += writtenBytesNow
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
