package domain

import (
	"fmt"
)

const (
	MESSAGE_TYPE_SIZE = 1 // u8
	PAYLOAD_LEN_SIZE  = 4 // u32
	HEADER_SIZE       = MESSAGE_TYPE_SIZE + PAYLOAD_LEN_SIZE
)

type MessageHeader struct {
	Type       MessageType
	PayloadLen uint32
}

func (h MessageHeader) Serialize() []byte {
	return []byte{
		byte(h.Type),
		byte(h.PayloadLen >> 24),
		byte(h.PayloadLen >> 16),
		byte(h.PayloadLen >> 8),
		byte(h.PayloadLen),
	}
}

func DeserializeHeader(buf []byte) (MessageHeader, error) {
	if len(buf) != HEADER_SIZE {
		return MessageHeader{}, fmt.Errorf("invalid header size: expected %d bytes, got %d", HEADER_SIZE, len(buf))
	}

	msgType := MessageType(buf[0])
	payloadLen := uint32(buf[1])<<24 |
		uint32(buf[2])<<16 |
		uint32(buf[3])<<8 |
		uint32(buf[4])

	return MessageHeader{
		Type:       msgType,
		PayloadLen: payloadLen,
	}, nil
}
