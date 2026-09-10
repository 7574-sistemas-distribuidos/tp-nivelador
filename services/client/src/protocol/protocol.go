package protocol

import (
	"encoding/binary"
	"io"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

const (
	MsgBet     byte = 1
	MsgAck     byte = 2
	MsgEndBets byte = 3
	MsgWinners byte = 4
)

const HeaderSize = 5

func SendMsg(socket io.Writer, msgType byte, payload []byte) error {
	header := make([]byte, HeaderSize)
	header[0] = msgType
	binary.BigEndian.PutUint32(header[1:], uint32(len(payload)))

	if err := safe_socket.SendAll(socket, header); err != nil {
		return err
	}
	if len(payload) > 0 {
		return safe_socket.SendAll(socket, payload)
	}
	return nil
}

func RecvMsg(socket io.Reader) (byte, []byte, error) {
	header, err := safe_socket.RecvAll(socket, HeaderSize)
	if err != nil {
		return 0, nil, err
	}
	msgType := header[0]
	length := binary.BigEndian.Uint32(header[1:])

	if length == 0 {
		return msgType, []byte{}, nil
	}

	payload, err := safe_socket.RecvAll(socket, int(length))
	if err != nil {
		return 0, nil, err
	}
	return msgType, payload, nil
}
