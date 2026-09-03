package domain

import (
	"bytes"
	"testing"
)

func TestCanSerializeMessageHeader(t *testing.T) {
	header := MessageHeader{
		Type:       MessageTypeBet,
		PayloadLen: 42,
	}

	serialized := header.Serialize()

	expected := []byte{
		byte(MessageTypeBet),
		0, 0, 0, 42,
	}

	if !bytes.Equal(serialized, expected) {
		t.Fatalf("test_0 can_serialize_message_header: expected %v, got %v", expected, serialized)
	}
}

func TestCanDeserializeMessageHeader(t *testing.T) {
	buf := []byte{
		byte(MessageTypeBet),
		0, 0, 0, 42,
	}

	header, err := DeserializeHeader(buf)

	if err != nil {
		t.Fatalf("can_deserialize_message_header: expected no error, got %v", err)
	}

	expected := MessageHeader{
		Type:       MessageTypeBet,
		PayloadLen: 42,
	}

	if header != expected {
		t.Fatalf("can_deserialize_message_header: expected %+v, got %+v", expected, header)
	}
}

func TestDeserializeHeaderShortReadReturnsError(t *testing.T) {
	buf := []byte{byte(MessageTypeBet), 0, 0}

	_, err := DeserializeHeader(buf)

	if err == nil {
		t.Fatal("deserialize_header_with_short_buffer_returns_error: expected error, got nil")
	}
}
