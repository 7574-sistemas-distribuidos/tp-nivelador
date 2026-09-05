package protocol

import (
	"io"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/domain"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

func SendMessage(writer io.Writer, message domain.Message) error {
	if err := safe_socket.SendAll(writer, message.Header.Serialize()); err != nil {
		return err
	}
	if err := safe_socket.SendAll(writer, message.Payload); err != nil {
		return err
	}
	return nil
}

func ReceiveMessage(reader io.Reader) (domain.MessageHeader, []byte, error) {
	headerBytes, err := safe_socket.RecvAll(reader, domain.HEADER_SIZE)
	if err != nil {
		return domain.MessageHeader{}, nil, err
	}
	header, err := domain.DeserializeHeader(headerBytes)
	if err != nil {
		return domain.MessageHeader{}, nil, err
	}

	payload, err := safe_socket.RecvAll(reader, int(header.PayloadLen))
	if err != nil {
		return header, nil, err
	}

	return header, payload, nil
}
