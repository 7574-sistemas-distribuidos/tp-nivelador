package protocol

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

func SerializeBet(p Bet, agencyId string) ([]byte, uint32, error) {
	if len(p.FirstName) > 255 || len(p.LastName) > 255 {
		logger.Error("SerializeBetFirstNameAndLastName", logger.Fail, " FirstName or LastName exceeds 255 characters")
		return nil, 0, errors.New("FirstName or LastName exceeds 255 characters")
	}

	var payload []byte

	agencyIdParsed, err := strconv.ParseUint(agencyId, 10, 8)

	if err != nil {
		logger.Error("SerializeBet", logger.Fail, " Failed to parse AgencyId: ", err)
		return nil, 0, err
	}
	payload = append(payload, byte(agencyIdParsed))

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

	return finalBuffer, totalLength, nil
}
