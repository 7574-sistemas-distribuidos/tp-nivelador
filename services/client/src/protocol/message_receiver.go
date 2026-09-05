package protocol

import (
	"encoding/binary"
	"errors"
	"io"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

func receiveWinnersMessage(socket io.Reader) ([]byte, error) {
	message_length_bytes, err := safe_socket.RecvAll(socket, 4)
	if err != nil {
		return nil, err
	}
	message_length := binary.BigEndian.Uint32(message_length_bytes)
	winning_bets, err := safe_socket.RecvAll(socket, int(message_length))
	if err != nil {
		return nil, err
	}
	return winning_bets, nil
}

func ReceiveMessage(socket io.Reader) ([]byte, error) {
	message_type_bytes, err := safe_socket.RecvAll(socket, 1)
	if err != nil {
		return nil, err
	}
	message_type := MessageType(message_type_bytes[0])

	if message_type == AckBetMessage {
		return nil, nil
	}
	if message_type == WinnersMessage {
		return receiveWinnersMessage(socket)
	}
	return nil, errors.New("unknown message type")
}
