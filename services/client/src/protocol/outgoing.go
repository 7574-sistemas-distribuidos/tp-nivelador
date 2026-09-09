package protocol

import (
	"fmt"
	"math"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/business"
)

type StartBetsSendingMessage struct {
	agencyId int
}

const agencyIdBytes = 1 // needed here because there's no domain representation for it

func NewStartBetsSendingMessageFrom(agencyId int) (*StartBetsSendingMessage, error) {
	if agencyId < 0 || agencyId > math.MaxUint8 {
		return nil, fmt.Errorf("agency id %d does not fit in %d byte", agencyId, agencyIdBytes)
	}
	return &StartBetsSendingMessage{agencyId: agencyId}, nil
}

func (message *StartBetsSendingMessage) Type() byte {
	return startBetsSendingType
}

func (message *StartBetsSendingMessage) Payload() []byte {
	return []byte{byte(message.agencyId)}
}

type FilledBetMessage struct {
	betRecord []byte
}

func NewFilledBetMessageFrom(bet business.Bet) (*FilledBetMessage, error) {
	betBytes, err := betToBytes(bet)
	if err != nil {
		return nil, err
	}
	return &FilledBetMessage{betRecord: betBytes}, nil
}

func (message *FilledBetMessage) Type() byte {
	return filledBetType
}

func (message *FilledBetMessage) Payload() []byte {
	return message.betRecord
}

type FinalizeBetsSendingMessage struct {
}

func (message *FinalizeBetsSendingMessage) Type() byte {
	return finalizeBetsSendingType
}

func (message *FinalizeBetsSendingMessage) Payload() []byte {
	return []byte{}
}

type OutgoingMessage interface {
	Type() byte
	Payload() []byte
}
