package protocol

import (
	"encoding/binary"
	"fmt"
	"math"
	"net"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

const (
	typeBytes   = 1
	lengthBytes = 2
)

const (
	startBetsSendingType          = 0x01
	filledBetsType                = 0x02
	finalizeBetsSendingType       = 0x03
	startBetWinnersSendingType    = 0x04
	betWinnerType                 = 0x05
	finalizeBetWinnersSendingType = 0x06
)

type MessageChannel struct {
	connection net.Conn
}

func NewMessageChannel(connection net.Conn) *MessageChannel {
	return &MessageChannel{connection: connection}
}

func (channel *MessageChannel) Send(message OutgoingMessage) error {
	payloadBytes := message.Payload()
	if len(payloadBytes) > math.MaxUint16 {
		return fmt.Errorf(
			"payload of %d bytes does not fit in the %d byte length field",
			len(payloadBytes), lengthBytes,
		)
	}

	frameBytes := make([]byte, 0, typeBytes+lengthBytes+len(payloadBytes))
	frameBytes = append(frameBytes, message.Type())
	frameBytes = binary.BigEndian.AppendUint16(frameBytes, uint16(len(payloadBytes)))
	frameBytes = append(frameBytes, payloadBytes...)

	return safe_socket.SendAll(channel.connection, frameBytes)
}

func (channel *MessageChannel) Receive() (IncomingMessage, error) {
	messageType, err := safe_socket.RecvAll(channel.connection, typeBytes)
	if err != nil {
		return nil, err
	}

	messageLength, err := safe_socket.RecvAll(channel.connection, lengthBytes)
	if err != nil {
		return nil, err
	}

	payloadLength := int(binary.BigEndian.Uint16(messageLength))
	payloadBytes, err := safe_socket.RecvAll(channel.connection, payloadLength)
	if err != nil {
		return nil, err
	}

	return incomingMessageFrom(messageType[0], payloadBytes)
}

func incomingMessageFrom(messageType byte, payloadBytes []byte) (IncomingMessage, error) {
	switch messageType {
	case startBetWinnersSendingType:
		return StartBetWinnersSendingMessageFrom(payloadBytes)
	case betWinnerType:
		return BetWinnerMessageFrom(payloadBytes)
	case finalizeBetWinnersSendingType:
		return FinalizeBetWinnersSendingMessageFrom(payloadBytes)
	default:
		return nil, fmt.Errorf("unknown message type 0x%02x", messageType)
	}
}
