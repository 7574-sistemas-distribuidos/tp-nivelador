package protocol

import (
	"encoding/binary"
	"strconv"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/entities"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
)

func GenerateBetPacket(bets []entities.Bet, agencyId string) ([]byte, error) {
	agencyIdParsed, err := strconv.ParseUint(agencyId, 10, 8)

	if err != nil {
		logger.Error("GeneratePacket", logger.Fail, " Failed to parse AgencyId: ", err)
		return nil, err
	}
	betsAmount := len(bets)
	payloadMaxLength := betsAmount * entities.BetSize()
	betsSerialized := make([]byte, 0, payloadMaxLength)

	for i, bet := range bets {

		betSerialized, err := entities.SerializeBet(bet)
		if err != nil {
			logger.Error("serialize-bet", logger.Fail, "agency-id", agencyId, "record-id", i, "err", err)
			return nil, err
		}
		betsSerialized = append(betsSerialized, betSerialized...)
	}

	payloadLength := len(betsSerialized)
	agencyIdBytes := uint8(agencyIdParsed)
	messageType := BetMessage
	header := NewHeader(agencyIdBytes, messageType)
	packet := make([]byte, 0, header.Size()+4+4+payloadLength)
	packet = append(packet, header.Serialize()...)
	betsAmountBytes := make([]byte, 4)
	binary.BigEndian.PutUint32(betsAmountBytes, uint32(betsAmount))
	packet = append(packet, betsAmountBytes...)
	payloadLengthBytes := make([]byte, 4)
	binary.BigEndian.PutUint32(payloadLengthBytes, uint32(payloadLength))
	packet = append(packet, payloadLengthBytes...)
	packet = append(packet, betsSerialized...)

	return packet, nil
}

func GenerateAllBetsSentPacket(agencyId string) ([]byte, error) {
	agencyIdParsed, err := strconv.ParseUint(agencyId, 10, 8)

	if err != nil {
		logger.Error("GeneratePacket", logger.Fail, " Failed to parse AgencyId: ", err)
		return nil, err
	}
	agencyIdBytes := uint8(agencyIdParsed)
	messageType := AllBetsSentMessage
	header := NewHeader(agencyIdBytes, messageType)
	allBetsSentSerialized := make([]byte, 0, header.Size())
	allBetsSentSerialized = append(allBetsSentSerialized, header.Serialize()...)
	return allBetsSentSerialized, nil
}
