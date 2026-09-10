package entities

import (
	"encoding/binary"
	"errors"
	"fmt"
	"strconv"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
)

type Bet struct {
	FirstName string
	LastName  string
	Id        uint32
	BirthDate string
	Numbers   uint32
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

	numbersParsed, err := strconv.ParseUint(record[4], 10, 32)
	if err != nil {
		logger.Error("NewBetFromRecord", logger.Fail, " Failed to parse Numbers: ", err)
		return Bet{}, err
	}

	return Bet{
		FirstName: record[0],
		LastName:  record[1],
		Id:        uint32(idParsed),
		BirthDate: record[3],
		Numbers:   uint32(numbersParsed),
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

	payload = binary.BigEndian.AppendUint32(payload, p.Numbers)

	var finalBuffer []byte
	totalLength := uint32(len(payload))
	finalBuffer = binary.BigEndian.AppendUint32(finalBuffer, totalLength)
	finalBuffer = append(finalBuffer, payload...)

	return finalBuffer, nil
}

func DeserializeBet(data []byte) (Bet, error) {
	offset := 0
	if len(data) < 1 {
		return Bet{}, fmt.Errorf("insufficient data for first name length")
	}
	firstNameLength := int(data[offset])
	offset += 1

	if len(data) < offset+firstNameLength+1 {
		return Bet{}, fmt.Errorf("insufficient data for first name or last name length")
	}
	firstName := string(data[offset : offset+firstNameLength])
	offset += firstNameLength

	lastNameLength := int(data[offset])
	offset += 1

	if len(data) < offset+lastNameLength+4+1 {
		return Bet{}, fmt.Errorf("insufficient data for last name, id or birthdate length")
	}
	lastName := string(data[offset : offset+lastNameLength])
	offset += lastNameLength

	id := binary.BigEndian.Uint32(data[offset : offset+4])
	offset += 4

	birthDateLength := int(data[offset])
	offset += 1

	if len(data) < offset+birthDateLength+2 {
		return Bet{}, fmt.Errorf("insufficient data for birthdate or numbers")
	}
	birthDate := string(data[offset : offset+birthDateLength])
	offset += birthDateLength

	numbers := binary.BigEndian.Uint32(data[offset : offset+4])

	logger.Info("DeserializeBet", logger.Success, " Successfully deserialized Bet struct from data")

	return Bet{
		FirstName: firstName,
		LastName:  lastName,
		Id:        id,
		BirthDate: birthDate,
		Numbers:   numbers,
	}, nil
}

func BetToRecord(bet Bet) []string {
	return []string{
		bet.FirstName,
		bet.LastName,
		strconv.FormatUint(uint64(bet.Id), 10),
		bet.BirthDate,
		strconv.FormatUint(uint64(bet.Numbers), 10),
	}
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
	return bets, nil
}

func BetSize() int {
	// 1 byte for FirstName length + FirstName bytes
	// 1 byte for LastName length + LastName bytes
	// 4 bytes for Id
	// 1 byte for BirthDate length + BirthDate bytes
	// 4 bytes for Numbers
	return 1 + 255 + 1 + 255 + 4 + 1 + 10 + 4 // Assuming max lengths for FirstName, LastName, and BirthDate
}
