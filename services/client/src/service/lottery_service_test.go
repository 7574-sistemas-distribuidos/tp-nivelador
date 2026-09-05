package service

import (
	"bytes"
	"strings"
	"testing"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/domain"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/protocol"
)

const AGENCY_ID = "1"

type fakeConnection struct {
	incoming *bytes.Buffer
	outgoing *bytes.Buffer
}

func newFakeConnection(responses ...domain.Message) *fakeConnection {
	incoming := &bytes.Buffer{}
	for _, response := range responses {
		protocol.SendMessage(incoming, response)
	}
	return &fakeConnection{incoming: incoming, outgoing: &bytes.Buffer{}}
}

func (connection *fakeConnection) Read(buf []byte) (int, error) {
	return connection.incoming.Read(buf)
}

func (connection *fakeConnection) Write(buf []byte) (int, error) {
	return connection.outgoing.Write(buf)
}

func sentBytes(messages ...domain.Message) []byte {
	buffer := &bytes.Buffer{}
	for _, message := range messages {
		protocol.SendMessage(buffer, message)
	}
	return buffer.Bytes()
}

func winnerMessage(bet domain.Bet) domain.Message {
	payload := []byte(strings.Join(bet.Fields(), ","))
	return domain.Message{
		Header:  domain.MessageHeader{Type: domain.MessageTypeWinner, PayloadLen: uint32(len(payload))},
		Payload: payload,
	}
}

func finishMessage() domain.Message {
	return domain.Message{
		Header:  domain.MessageHeader{Type: domain.MessageTypeFinish, PayloadLen: 0},
		Payload: nil,
	}
}

func aBet() domain.Bet {
	return domain.Bet{
		FirstName: "Santiago Lionel",
		LastName:  "Lorca",
		Document:  "30904465",
		BirthDate: "1999-03-17",
		Number:    "7574",
	}
}

func TestSendBetSendsBetMessageAndConsumesAck(t *testing.T) {
	bet := aBet()
	connection := newFakeConnection(domain.AckMessage())
	service := NewLotteryService(connection, AGENCY_ID)

	if err := service.SendBet(bet); err != nil {
		t.Fatalf("send_bet_sends_bet_message_and_consumes_ack: expected no error, got %v", err)
	}

	expected := sentBytes(domain.BetMessage(AGENCY_ID, bet))
	if !bytes.Equal(connection.outgoing.Bytes(), expected) {
		t.Fatalf("send_bet_sends_bet_message_and_consumes_ack: expected %v, got %v", expected, connection.outgoing.Bytes())
	}
	if connection.incoming.Len() != 0 {
		t.Fatalf("send_bet_sends_bet_message_and_consumes_ack: expected ack to be consumed, got %d pending bytes", connection.incoming.Len())
	}
}

func TestSendBetFailsWhenResponseIsNotAck(t *testing.T) {
	connection := newFakeConnection(finishMessage())
	service := NewLotteryService(connection, AGENCY_ID)

	if err := service.SendBet(aBet()); err == nil {
		t.Fatal("send_bet_fails_when_response_is_not_ack: expected error, got nil")
	}
}

func TestSendBetFailsWhenConnectionIsClosed(t *testing.T) {
	connection := newFakeConnection()
	service := NewLotteryService(connection, AGENCY_ID)

	if err := service.SendBet(aBet()); err == nil {
		t.Fatal("send_bet_fails_when_connection_is_closed: expected error, got nil")
	}
}

func TestNotifyAwaitingWinnersSendsMessageAndConsumesAck(t *testing.T) {
	connection := newFakeConnection(domain.AckMessage())
	service := NewLotteryService(connection, AGENCY_ID)

	if err := service.NotifyAwaitingWinners(); err != nil {
		t.Fatalf("notify_awaiting_winners_sends_message_and_consumes_ack: expected no error, got %v", err)
	}

	expected := sentBytes(domain.AwaitingWinnersMessage(AGENCY_ID))
	if !bytes.Equal(connection.outgoing.Bytes(), expected) {
		t.Fatalf("notify_awaiting_winners_sends_message_and_consumes_ack: expected %v, got %v", expected, connection.outgoing.Bytes())
	}
}

func TestReadWinnersReturnsBetsUntilFinish(t *testing.T) {
	winner := aBet()
	connection := newFakeConnection(winnerMessage(winner), winnerMessage(winner), finishMessage())
	service := NewLotteryService(connection, AGENCY_ID)

	winners, err := service.ReadWinners()

	if err != nil {
		t.Fatalf("read_winners_returns_bets_until_finish: expected no error, got %v", err)
	}
	if len(winners) != 2 {
		t.Fatalf("read_winners_returns_bets_until_finish: expected 2 winners, got %d", len(winners))
	}
	if winners[0] != winner {
		t.Fatalf("read_winners_returns_bets_until_finish: expected %+v, got %+v", winner, winners[0])
	}

	expected := sentBytes(domain.AckMessage(), domain.AckMessage(), domain.AckMessage())
	if !bytes.Equal(connection.outgoing.Bytes(), expected) {
		t.Fatalf("read_winners_returns_bets_until_finish: expected an ack per winner plus the finish ack, got %v", connection.outgoing.Bytes())
	}
}

func TestReadWinnersWithoutWinnersReturnsEmptyList(t *testing.T) {
	connection := newFakeConnection(finishMessage())
	service := NewLotteryService(connection, AGENCY_ID)

	winners, err := service.ReadWinners()

	if err != nil {
		t.Fatalf("read_winners_without_winners_returns_empty_list: expected no error, got %v", err)
	}
	if len(winners) != 0 {
		t.Fatalf("read_winners_without_winners_returns_empty_list: expected 0 winners, got %d", len(winners))
	}
}

func TestReadWinnersFailsOnUnexpectedMessageType(t *testing.T) {
	connection := newFakeConnection(domain.BetMessage(AGENCY_ID, aBet()))
	service := NewLotteryService(connection, AGENCY_ID)

	winners, err := service.ReadWinners()

	if err == nil {
		t.Fatal("read_winners_fails_on_unexpected_message_type: expected error, got nil")
	}
	if winners != nil {
		t.Fatalf("read_winners_fails_on_unexpected_message_type: expected no partial winners, got %+v", winners)
	}
}
