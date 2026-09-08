package entities

import (
	"encoding/binary"
	"errors"
	"strconv"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
)

type Bet struct {
	FirstName string
	LastName  string
	Id        uint32
	BirthDate string
	Numbers   uint16
}

func NewBetFromRecord(record []string) (Bet, error) {
	if len(record) < 5 {
		logger.Error("NewBetFromRecord", logger.Fail, " Record does not have enough fields")
		return Bet{}, errors.New("record does not have enough fields")
	}

	idParsed, err := strconv.ParseUint(record[2], 10, 32)
	if err != nil {
		logger.Error("NewBetFromRecord", logger.Fail, " Failed to parse ID: ", err)
		return Bet{}, err
	}

	numbersParsed, err := strconv.ParseUint(record[4], 10, 16)
	if err != nil {
		logger.Error("NewBetFromRecord", logger.Fail, " Failed to parse Numbers: ", err)
		return Bet{}, err
	}

	logger.Info("NewBetFromRecord", logger.Success, " Successfully created Bet struct from record")

	return Bet{
		FirstName: record[0],
		LastName:  record[1],
		Id:        uint32(idParsed),
		BirthDate: record[3],
		Numbers:   uint16(numbersParsed),
	}, nil
}

func SerializeBet(p Bet) ([]byte, error) {
	if len(p.FirstName) > 255 || len(p.LastName) > 255 {
		logger.Error("SerializeBetFirstNameAndLastName", logger.Fail, " FirstName or LastName exceeds 255 characters")
		return nil, errors.New("FirstName or LastName exceeds 255 characters")
	}

	var payload []byte

	payload = append(payload, uint8(len(p.FirstName)))
	payload = append(payload, p.FirstName...)

	payload = append(payload, byte(len(p.LastName)))
	payload = append(payload, p.LastName...)

	payload = binary.BigEndian.AppendUint32(payload, p.Id)

	payload = append(payload, uint8(len(p.BirthDate)))
	payload = append(payload, p.BirthDate...)

	payload = binary.BigEndian.AppendUint16(payload, p.Numbers)

	var finalBuffer []byte
	totalLength := uint32(len(payload))
	finalBuffer = binary.BigEndian.AppendUint32(finalBuffer, totalLength)
	finalBuffer = append(finalBuffer, payload...)
	logger.Info("SerializeBet", logger.Success, " Successfully serialized Bet struct")

	return finalBuffer, nil
}

func BetsFromRecords(records [][]string) ([]Bet, error) {
	bets := make([]Bet, 0, len(records))
	for i, record := range records {
		bet, err := NewBetFromRecord(record)
		if err != nil {
			logger.Error("BetsFromRecords", logger.Fail, " Failed to create Bet from record at index ", i, ": ", err)
			return nil, err
		}
		bets = append(bets, bet)
	}
	logger.Info("BetsFromRecords", logger.Success, " Successfully created Bet structs from records")
	return bets, nil
}

func BetSize() int {
	// 1 byte for FirstName length + FirstName bytes
	// 1 byte for LastName length + LastName bytes
	// 4 bytes for Id
	// 1 byte for BirthDate length + BirthDate bytes
	// 2 bytes for Numbers
	return 1 + 255 + 1 + 255 + 4 + 1 + 10 + 2 // Assuming max lengths for FirstName, LastName, and BirthDate
}
