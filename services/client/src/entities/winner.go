package entities

import (
	"encoding/binary"
	"strconv"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
)

type Winner struct {
	FirstName string
	LastName  string
	social_id uint32
}

func DeserializeWinner(data []byte) (Winner, error) {
	offset := 0
	firstNameLength := int(data[offset])

	offset += 1
	fiirstName := string(data[offset : offset+firstNameLength])

	offset += firstNameLength
	lastNameLength := int(data[offset])

	offset += 1
	lastName := string(data[offset : offset+lastNameLength])

	offset += lastNameLength
	social_id := binary.BigEndian.Uint32(data[offset : offset+4])

	logger.Info("DeserializeWinner", logger.Success, " Successfully deserialized Winner struct from data")

	return Winner{
		FirstName: fiirstName,
		LastName:  lastName,
		social_id: social_id,
	}, nil

}

func WinnerToRecord(winner Winner) []string {
	var record []string
	record = append(record, winner.FirstName)
	record = append(record, winner.LastName)
	tmp := strconv.FormatUint(uint64(winner.social_id), 10)
	record = append(record, tmp)
	return record

}
