package protocol

import (
	"net"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/domain"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

func SendMessage(conn net.Conn, message domain.Message) error {
	if err := safe_socket.SendAll(conn, message.Header.Serialize()); err != nil {
		return err
	}
	if err := safe_socket.SendAll(conn, message.Payload); err != nil {
		return err
	}
	return nil
}

func ReceiveMessage(conn net.Conn) (domain.MessageHeader, []byte, error) {
	headerBytes, err := safe_socket.RecvAll(conn, domain.HEADER_SIZE)
	if err != nil {
		return domain.MessageHeader{}, nil, err
	}
	header, err := domain.DeserializeHeader(headerBytes)
	if err != nil {
		return domain.MessageHeader{}, nil, err
	}

	payload, err := safe_socket.RecvAll(conn, int(header.PayloadLen))
	if err != nil {
		return header, nil, err
	}

	return header, payload, nil
}
