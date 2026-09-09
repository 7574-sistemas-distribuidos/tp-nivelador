package protocol

import (
	"encoding/binary"
	"fmt"
	"math"
	"unicode/utf8"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/business"
)

const (
	documentBytes   = 4
	numberBytes     = 2
	birthdateBytes  = 10
	nameLengthBytes = 1

	fixedPrefixBytes   = documentBytes + numberBytes + birthdateBytes
	minimumRecordBytes = fixedPrefixBytes + nameLengthBytes
)

func betToBytes(bet business.Bet) ([]byte, error) {
	if int64(bet.Document) > math.MaxUint32 {
		return nil, fmt.Errorf("document %d does not fit in %d bytes", bet.Document, documentBytes)
	}
	if bet.Number > math.MaxUint16 {
		return nil, fmt.Errorf("number %d does not fit in %d bytes", bet.Number, numberBytes)
	}
	if len(bet.Birthdate) != birthdateBytes {
		return nil, fmt.Errorf(
			"birthdate must be exactly %d bytes, got %d: %q",
			birthdateBytes, len(bet.Birthdate), bet.Birthdate,
		)
	}
	if len(bet.FirstName) > math.MaxUint8 {
		return nil, fmt.Errorf(
			"first_name is %d bytes, at most %d fit in the length prefix",
			len(bet.FirstName), math.MaxUint8,
		)
	}
	if len(bet.LastName) > math.MaxUint8 {
		return nil, fmt.Errorf(
			"last_name is %d bytes, at most %d fit in the length prefix",
			len(bet.LastName), math.MaxUint8,
		)
	}

	totalRecordBytes := fixedPrefixBytes + 2*nameLengthBytes + len(bet.FirstName) + len(bet.LastName)

	recordBytes := make([]byte, 0, totalRecordBytes)
	recordBytes = binary.BigEndian.AppendUint32(recordBytes, uint32(bet.Document))
	recordBytes = binary.BigEndian.AppendUint16(recordBytes, uint16(bet.Number))
	recordBytes = append(recordBytes, bet.Birthdate...)
	recordBytes = append(recordBytes, byte(len(bet.FirstName)))
	recordBytes = append(recordBytes, bet.FirstName...)
	recordBytes = append(recordBytes, byte(len(bet.LastName)))
	recordBytes = append(recordBytes, bet.LastName...)

	return recordBytes, nil
}

func betFromBytes(payload []byte) (business.Bet, error) {
	if len(payload) < minimumRecordBytes {
		return business.Bet{}, fmt.Errorf(
			"bet record needs at least %d bytes, got %d",
			minimumRecordBytes, len(payload),
		)
	}

	offset := 0
	document := binary.BigEndian.Uint32(payload[offset : offset+documentBytes])
	offset += documentBytes

	number := binary.BigEndian.Uint16(payload[offset : offset+numberBytes])
	offset += numberBytes

	birthdate, err := decodedText(payload[offset:offset+birthdateBytes], "birthdate")
	if err != nil {
		return business.Bet{}, err
	}
	offset += birthdateBytes

	firstNameLength := int(payload[offset])
	offset += nameLengthBytes
	if offset+firstNameLength+nameLengthBytes > len(payload) {
		return business.Bet{}, fmt.Errorf(
			"first_name length %d overruns the record: only %d bytes remain",
			firstNameLength, len(payload)-offset,
		)
	}
	firstName, err := decodedText(payload[offset:offset+firstNameLength], "first_name")
	if err != nil {
		return business.Bet{}, err
	}
	offset += firstNameLength

	lastNameLength := int(payload[offset])
	offset += nameLengthBytes
	if offset+lastNameLength != len(payload) {
		return business.Bet{}, fmt.Errorf(
			"last_name length %d does not consume the record exactly: %d bytes remain",
			lastNameLength, len(payload)-offset,
		)
	}
	lastName, err := decodedText(payload[offset:offset+lastNameLength], "last_name")
	if err != nil {
		return business.Bet{}, err
	}

	return business.Bet{
		Document:  int(document),
		Number:    int(number),
		Birthdate: birthdate,
		FirstName: firstName,
		LastName:  lastName,
	}, nil
}

// python bytes.decode("utf-8") raises on invalid bytes, since go's doesn't have this capability
// placing this helper here to handle that scenario
func decodedText(raw []byte, field string) (string, error) {
	if !utf8.Valid(raw) {
		return "", fmt.Errorf("%s is not valid utf-8", field)
	}
	return string(raw), nil
}
