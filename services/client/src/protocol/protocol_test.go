package protocol

import (
	"bytes"
	"testing"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/domain"
)

func TestCanSendMessageUsingProtocol(t *testing.T) {
	bet := domain.Bet{
		FirstName: "Santiago Lionel",
		LastName:  "Lorca",
		Document:  "30904465",
		BirthDate: "1999-03-17",
		Number:    "7574",
	}
	message := domain.BetMessage("1", bet)
	buffer := &bytes.Buffer{}

	if err := SendMessage(buffer, message); err != nil {
		t.Fatalf("can_send_message_using_protocol: expected no error, got %v", err)
	}

	expected := append(message.Header.Serialize(), message.Payload...)
	if !bytes.Equal(buffer.Bytes(), expected) {
		t.Fatalf("can_send_message_using_protocol: expected %v, got %v", expected, buffer.Bytes())
	}
}

func TestCanReceiveMessageUsingProtocol(t *testing.T) {
	message := domain.AwaitingWinnersMessage("1")
	buffer := &bytes.Buffer{}
	if err := SendMessage(buffer, message); err != nil {
		t.Fatalf("can_receive_message_using_protocol: expected no error, got %v", err)
	}

	header, payload, err := ReceiveMessage(buffer)

	if err != nil {
		t.Fatalf("can_receive_message_using_protocol: expected no error, got %v", err)
	}
	if header != message.Header {
		t.Fatalf("can_receive_message_using_protocol: expected %+v, got %+v", message.Header, header)
	}
	if !bytes.Equal(payload, message.Payload) {
		t.Fatalf("can_receive_message_using_protocol: expected %v, got %v", message.Payload, payload)
	}
}

func TestReceiveMessageOnClosedStreamReturnsError(t *testing.T) {
	if _, _, err := ReceiveMessage(&bytes.Buffer{}); err == nil {
		t.Fatal("receive_message_on_closed_stream_returns_error: expected error, got nil")
	}
}
