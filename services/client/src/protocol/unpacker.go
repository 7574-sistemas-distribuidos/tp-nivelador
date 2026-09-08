package protocol

import (
	"encoding/binary"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/entities"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
)

func UnpackWinners(winners []byte) ([]entities.Winner, error) {
	logger.Info("unpack-winners", logger.InProgress)
	offset := 0
	winnersAmount := binary.BigEndian.Uint32(winners[offset : offset+4])
	offset += 4
	logger.Info("unpack-winners", logger.InProgress, "winners-amount", winnersAmount)
	var winnersList []entities.Winner

	for range winnersAmount {
		winnerLength := binary.BigEndian.Uint32(winners[offset : offset+4])
		offset += 4
		logger.Info("unpack-winners", logger.InProgress, "winner-length", winnerLength)
		winnerData := winners[offset : offset+int(winnerLength)]
		winner, err := entities.DeserializeWinner(winnerData)
		if err != nil {
			return nil, err
		}
		winnersList = append(winnersList, winner)
		offset += int(winnerLength)
	}
	logger.Info("unpack-winners", logger.Success, "winners-amount", winnersAmount)
	return winnersList, nil
}

func UnpackMessageType(message []byte) (bool, error) {
	if MessageType(message[0]) == WinnersMessage {
		return true, nil
	}
	if MessageType(message[0]) == FinalizeMessage {
		return true, nil
	}
	if MessageType(message[0]) == AckBetMessage {
		return true, nil
	}
	return false, nil
}
