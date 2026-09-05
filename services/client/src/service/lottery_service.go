package service

import (
	"errors"
	"fmt"
	"io"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/domain"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/protocol"
)

type LotteryService struct {
	conn     io.ReadWriter
	agencyId string
}

func NewLotteryService(conn io.ReadWriter, agencyId string) *LotteryService {
	return &LotteryService{conn: conn, agencyId: agencyId}
}

func (service *LotteryService) SendBet(bet domain.Bet) error {
	message := domain.BetMessage(service.agencyId, bet)
	if err := protocol.SendMessage(service.conn, message); err != nil {
		return err
	}
	return service.readAck()
}

func (service *LotteryService) NotifyAwaitingWinners() error {
	message := domain.AwaitingWinnersMessage(service.agencyId)
	if err := protocol.SendMessage(service.conn, message); err != nil {
		return err
	}
	return service.readAck()
}

func (service *LotteryService) ReadWinners() ([]domain.Bet, error) {
	var winners []domain.Bet

	for {
		header, payload, err := protocol.ReceiveMessage(service.conn)
		if err != nil {
			// Ante un error el stream quedo incompleto: se descartan las parciales.
			return nil, err
		}

		switch header.Type {
		case domain.MessageTypeWinner:
			bet, betErr := domain.ParseBetLine(string(payload))
			if betErr != nil {
				return nil, betErr
			}
			winners = append(winners, bet)

			if ackErr := service.sendAck(); ackErr != nil {
				return nil, ackErr
			}
		case domain.MessageTypeFinish:
			// Se confirma el cierre para que el server no corte sobre un socket a medio leer.
			if ackErr := service.sendAck(); ackErr != nil {
				return nil, ackErr
			}
			return winners, nil
		default:
			return nil, fmt.Errorf("unexpected message type while reading winners: %d", header.Type)
		}
	}
}

func (service *LotteryService) sendAck() error {
	return protocol.SendMessage(service.conn, domain.AckMessage())
}

func (service *LotteryService) readAck() error {
	header, _, err := protocol.ReceiveMessage(service.conn)
	if err != nil {
		return err
	}
	if header.Type != domain.MessageTypeAck {
		return errors.New("expected ack message type, got different type")
	}
	return nil
}
