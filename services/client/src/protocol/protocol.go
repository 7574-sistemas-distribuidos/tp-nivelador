package protocol

import (
	"net"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

const (
	MESSAGE_TYPE_SIZE = 1 // u8
	PAYLOAD_LEN_SIZE  = 4 // u32
	HEADER_SIZE       = MESSAGE_TYPE_SIZE + PAYLOAD_LEN_SIZE
)

func SendMessage(conn net.Conn, msgType MessageType, payload []byte) error {
	header := MessageHeader{msgType, uint32(len(payload))}
	if err := safe_socket.SendAll(conn, header.Serialize()); err != nil {
		return err
	}
	if err := safe_socket.SendAll(conn, payload); err != nil {
		return err
	}
	return nil
}

func ReceiveMessage(conn net.Conn) (MessageHeader, []byte, error) {
	headerBytes, err := safe_socket.RecvAll(conn, HEADER_SIZE)
	if err != nil {
		return MessageHeader{}, nil, err
	}
	header, err := DeserializeHeader(headerBytes)
	if err != nil {
		return MessageHeader{}, nil, err
	}

	payload, err := safe_socket.RecvAll(conn, int(header.PayloadLen))
	if err != nil {
		return header, nil, err
	}

	return header, payload, nil
}
