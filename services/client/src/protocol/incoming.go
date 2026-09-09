package protocol

import (
	"fmt"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/business"
)

type IncomingMessage interface {
	isIncomingMessage()
}

func (*StartBetWinnersSendingMessage) isIncomingMessage()    {}
func (*BetWinnerMessage) isIncomingMessage()                 {}
func (*FinalizeBetWinnersSendingMessage) isIncomingMessage() {}

type StartBetWinnersSendingMessage struct {
}

func StartBetWinnersSendingMessageFrom(payloadBytes []byte) (*StartBetWinnersSendingMessage, error) {
	if len(payloadBytes) != 0 {
		return nil, fmt.Errorf("start_bet_winners_sending carries no payload, got %d bytes", len(payloadBytes))
	}
	return &StartBetWinnersSendingMessage{}, nil
}

type BetWinnerMessage struct {
	bet business.Bet
}

func BetWinnerMessageFrom(payloadBytes []byte) (*BetWinnerMessage, error) {
	bet, err := betFromBytes(payloadBytes)
	if err != nil {
		return nil, err
	}
	return &BetWinnerMessage{bet: bet}, nil
}

func (message *BetWinnerMessage) Bet() business.Bet {
	return message.bet
}

type FinalizeBetWinnersSendingMessage struct {
}

func FinalizeBetWinnersSendingMessageFrom(payloadBytes []byte) (*FinalizeBetWinnersSendingMessage, error) {
	if len(payloadBytes) != 0 {
		return nil, fmt.Errorf("finalize_bet_winners_sending carries no payload, got %d bytes", len(payloadBytes))
	}
	return &FinalizeBetWinnersSendingMessage{}, nil
}
